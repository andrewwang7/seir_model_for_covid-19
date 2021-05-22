import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import seaborn as sns
import datetime
import requests
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
import os

from EstimationInfectedPeople import EstimationInfectedPeople


http_link = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
# ref: https://github.com/CSSEGISandData/COVID-19
#
filename_confirmed = 'time_series_covid19_confirmed_global.csv'
filename_deaths = 'time_series_covid19_deaths_global.csv'
filename_recovered = 'time_series_covid19_recovered_global.csv'
optim_days = 40   # None, 60, 30,
optim_weight_en = 0
SEIR_en = 1
show_day = 20
latent_period = 5.5
ratio_population = 0.0003  #0.001~0.0001  # for adjust contact population

# population:
# https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)
# https://simple.wikipedia.org/wiki/List_of_U.S._states_by_population

#check_Country =  ['Taiwan*', 'Singapore', 'Korea, South', 'China',     'China', 'Italy', 'US', 'US',         'US',       'US',         'US',             'France', 'Germany', 'Spain']
#check_Province = [None ,     None ,       None ,          'Hong Kong', 'Hubei', None,    None, 'Washington', 'New York', 'California', 'Massachusetts',  None ,    None ,     None ,]

#'''
check_Country    = ['Taiwan*', ]
check_Province   = [None ,     ]
check_population = [23600903,  ]
check_day_start   = ['2021-05-05']

#'''
'''
check_Country =  ['US',]
check_Province = [None, ]
check_population = [329064917,]
'''
'''
check_Country =  ['Taiwan*',]
check_Province = [ None,  ]
check_population = [23600903,]
'''
'''
check_Country =  ['Korea, South']
check_Province = [ None,  ]
check_population = [52000000,]
'''
'''
check_Country =  ['Singapore',]
check_Province = [ None,  ]
check_population = [5757499,]
'''
'''
check_Country =  ['Italy',]
check_Province = [ None,  ]
check_population = [60627291,]
'''
'''
check_Country =  ['Japan',]
check_Province = [ None,  ]
check_population = [126860301,]
'''
'''
check_Country =  ['Malaysia',]
check_Province = [ None,  ]
check_population = [32365999,]
'''

data_path = os.path.join('.', '~data')
result_path = os.path.join('.', '~result')


# download file
def main():
    # step 0: env
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    if not os.path.exists(result_path):
        os.mkdir(result_path)

    # step1: download
    donwload_csv(http_link + filename_confirmed, os.path.join(data_path, filename_confirmed))
    donwload_csv(http_link + filename_deaths, os.path.join(data_path, filename_deaths))
    donwload_csv(http_link + filename_recovered, os.path.join(data_path, filename_recovered))

    # step2: read
    pd_confirmed = pd.read_csv(os.path.join(data_path, filename_confirmed))
    pd_deaths = pd.read_csv(os.path.join(data_path, filename_deaths))
    pd_recovered = pd.read_csv(os.path.join(data_path, filename_recovered))

    # step3: plot
    for i_check_Country, i_check_Province, i_population, i_last_day in zip(check_Country, check_Province, check_population, check_day_start):
        if(i_check_Province is None):
            title = i_check_Country
        else:
            title = i_check_Country + '-' + i_check_Province

        print('------------------------------------')
        print(title)

        pd_covid_19 = data_preprocessing(pd_confirmed, pd_deaths, pd_recovered, i_check_Country, i_check_Province, i_last_day)


        #-----------------------------------
        # SEIR
        if(SEIR_en==1):
            SEIR = EstimationInfectedPeople(title, i_population, pd_covid_19,
                                            latent_period=latent_period, ratio_population=ratio_population, optim_days = optim_days, optim_weight_en = optim_weight_en )
            estParams = SEIR.getEstimatedParams()
            print(estParams)
            SEIR.print_estimation(estParams)

            fig = plt.figure(figsize=(20, 10), dpi=200)
            ax = fig.add_subplot(1, 1, 1)
            fig.suptitle('Infections of a new coronavirus in ' + title.strip('*'), fontsize=30)
            SEIR.plot_bar(ax)
            SEIR.save_plot('observed', result_path)
            ax.clear()

            SEIR.plot(ax, estParams)
            SEIR.save_plot('estimation', result_path)
            ax.clear()

        # ------------------------------
        # plot and save
        SEIR.pd_covid_19['new confirmed case'] = SEIR.pd_covid_19['confirmed'].diff()
        if (SEIR_en == 1):
            SEIR.pd_covid_19['estimation_confirmed']
            SEIR.pd_covid_19['new confirmed case (estimated)'] = SEIR.pd_covid_19['estimation_confirmed'].diff()


        fig, axes1 = plt.subplots()
        axes1.bar(SEIR.pd_covid_19.index, SEIR.pd_covid_19['new confirmed case'],
                  color='b', label='new confirmed case ')

        if (SEIR_en == 1):
            axes1.plot(SEIR.pd_covid_19.index, SEIR.pd_covid_19['new confirmed case (estimated)'],
                          color='r', label='new confirmed case (estimation)')

        '''
        axes1.set_ylabel('new confirmed case')

        axes2 = plt.twinx()
        axes2.plot(SEIR.pd_covid_19.index, SEIR.pd_covid_19['confirmed'], color='r', label='confirmed')
        axes2.set_ylabel('confirmed cases')
        '''

        axes1.xaxis.set_major_locator(MultipleLocator(show_day))
        axes1.xaxis.set_minor_locator(MultipleLocator(1))


        plt.title(title)
        #plt.show()
        plt.legend(loc="upper right", )
        plt.savefig(os.path.join(result_path, title.strip('*') + ".png"))

        idx_max = SEIR.pd_covid_19['new confirmed case (estimated)'].argmax()
        max_date = SEIR.pd_covid_19['new confirmed case (estimated)'].index[idx_max]
        max_new_case = SEIR.pd_covid_19['new confirmed case (estimated)'][max_date]
        print(f'Max estimated new case: {int(max_new_case)} at {max_date}')


def data_preprocessing(pd_confirmed, pd_deaths, pd_recovered, check_Country, check_Province, check_day_start):
    pd_confirmed_sel = get_pd_sel_country(pd_confirmed, check_Country, check_Province, 'confirmed')
    pd_deaths_sel = get_pd_sel_country(pd_deaths, check_Country, check_Province, 'deaths')
    pd_recovered_sel = get_pd_sel_country(pd_recovered, check_Country, check_Province, 'recovered')

    pd_covid_19 = pd.concat([pd_confirmed_sel, pd_deaths_sel, pd_recovered_sel], axis = 1)
    pd_covid_19.index = pd.to_datetime(pd_covid_19.index)


    if check_day_start is not None:
        check_day_start = datetime.datetime.strptime(check_day_start, "%Y-%m-%d")
        pd_covid_19 = pd_covid_19[pd_covid_19.index>=check_day_start]
        pd_covid_19 = pd_covid_19 - pd_covid_19.iloc[0]

    return pd_covid_19



def get_pd_sel_country(pd_data, check_Country, check_Province, name):
    if (check_Province is None):
        data_sel = (pd_data['Country/Region'] == check_Country)
    else:
        data_sel = (pd_data['Country/Region'] == check_Country) & (pd_data['Province/State'] == check_Province)

    if (check_Province is None):
        pd_sel = pd_data[(pd_data['Country/Region'] == check_Country)]
    else:
        pd_sel = pd_data[(pd_data['Country/Region'] == check_Country) & (pd_data['Province/State'] == check_Province)]

    # ------------------------------
    # to np or list
    pd_sel = pd_sel.drop('Province/State', axis=1)
    pd_sel = pd_sel.drop('Country/Region', axis=1)
    pd_sel = pd_sel.drop('Lat', axis=1)
    pd_sel = pd_sel.drop('Long', axis=1)


    if (pd_sel.values.shape[0] > 1):
        pd_sel = pd_sel.sum()

    pd_sel_series = pd_sel.iloc[0]
    pd_sel_series.name = name

    return pd_sel_series



def donwload_csv(donwload_url, save_filename):
    r=requests.get(donwload_url)
    with open(save_filename,"wb") as f:
        f.write(r.content)
    f.close()


#==============================================
if __name__ == '__main__':
    main()