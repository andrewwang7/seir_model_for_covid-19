import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
import os

from EstimationInfectedPeople import EstimationInfectedPeople


http_link = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
# ref: https://github.com/CSSEGISandData/COVID-19
filename_confirmed = 'time_series_19-covid-Confirmed.csv'
filename_deaths = 'time_series_19-covid-Deaths.csv'
filename_recovered = 'time_series_19-covid-Recovered.csv'
optim_days = 30   # None, 60, 30,
optim_weight_en = 0
SEIR_en = 1

# population:
# https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)
# https://simple.wikipedia.org/wiki/List_of_U.S._states_by_population

#check_Country =  ['Taiwan*', 'Singapore', 'Korea, South', 'China',     'China', 'Italy', 'US', 'US',         'US',       'US',         'US',             'France', 'Germany', 'Spain']
#check_Province = [None ,     None ,       None ,          'Hong Kong', 'Hubei', None,    None, 'Washington', 'New York', 'California', 'Massachusetts',  None ,    None ,     None ,]

'''
check_Country    = ['Taiwan*', 'Korea, South', 'Singapore', 'China',    'Italy',]    #'US',       'US', ]
check_Province   = [None ,     None ,          None,        'Hong Kong', None, ]     #'New York', None, ]
check_population = [23600903,  52000000,       5757499,     7479971,     60627291,]  #19453561,   329064917]
'''
'''
check_Country =  ['US',]
check_Province = [None, ]
population = [329064917,]
'''
'''
check_Country =  ['US',]
check_Province = [ 'New York',  ]
population = [19453561,]
'''
'''
check_Country =  ['US',]
check_Province = [ 'Washington',  ]
population = [7614893,]
'''
#'''
check_Country =  ['Taiwan*',]
check_Province = [ None,  ]
population = [23600903,]
#'''
'''
check_Country =  ['Korea, South']
check_Province = [ None,  ]
population = [52000000,]
'''
'''
check_Country =  ['Singapore',]
check_Province = [ None,  ]
population = [5757499,]
'''
'''
check_Country =  ['Italy',]
check_Province = [ None,  ]
population = [60627291,]
'''
'''
check_Country =  ['Japan',]
check_Province = [ None,  ]
population = [126860301,]
'''
'''
check_Country =  ['Malaysia',]
check_Province = [ None,  ]
population = [32365999,]
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
    for i_check_Country, i_check_Province, i_population in zip(check_Country, check_Province, check_population):
        if(i_check_Province is None):
            title = i_check_Country
        else:
            title = i_check_Country + '-' + i_check_Province

        print('------------------------------------')
        print(title)

        daily_timestamp_confirmed, daily_value_confirmed = get_pd2list(pd_confirmed, i_check_Country, i_check_Province)
        daily_timestamp_deaths, daily_value_deaths = get_pd2list(pd_deaths, i_check_Country, i_check_Province)
        daily_timestamp_recovered, daily_value_recovered = get_pd2list(pd_recovered, i_check_Country, i_check_Province)

        #-----------------------------------
        # SEIR
        if(SEIR_en==1):
            SEIR = EstimationInfectedPeople(title, i_population,
                                            daily_timestamp_confirmed, daily_value_confirmed, daily_value_deaths, daily_value_recovered,
                                            optim_days = optim_days, optim_weight_en = optim_weight_en )
            estParams = SEIR.getEstimatedParams()
            print(estParams)
            SEIR.print_estimation(estParams)

            fig = plt.figure(figsize=(20, 10), dpi=200)
            ax = fig.add_subplot(1, 1, 1)
            fig.suptitle('Infections of a new coronavirus in ' + title.strip('*'), fontsize=30)
            SEIR.plot_bar(ax)
            SEIR.save_plot('observed', result_path)

            SEIR.plot(ax, estParams)
            SEIR.save_plot('estimation', result_path)
            ax.clear()

        # ------------------------------
        # plot and save
        daily_value_confirmed_diff = np.append([0], np.diff(daily_value_confirmed))
        fig, axes1 = plt.subplots()

        axes1.bar(daily_timestamp_confirmed, daily_value_confirmed_diff, color='b', label='increased confirmed')
        axes1.set_ylabel('increased confirmed cases')

        axes2 = plt.twinx()
        axes2.plot(daily_timestamp_confirmed, daily_value_confirmed, color='r', label='confirmed')
        axes2.set_ylabel('confirmed cases')

        axes2.xaxis.set_major_locator(MultipleLocator(7))
        axes2.xaxis.set_minor_locator(MultipleLocator(1))

        plt.title(title)
        #plt.show()
        plt.savefig(os.path.join(result_path, title.strip('*') + ".png"))



def get_pd2list(pd_data, check_Country, check_Province):
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
    daily_timestamp = pd_sel.columns.tolist()
    if (pd_sel.values.shape[0] == 1):
        daily_value = pd_sel.values[0]
    else:
        daily_value = np.sum(pd_sel.values, axis=0)

    return daily_timestamp, daily_value

def donwload_csv(donwload_url, save_filename):
    r=requests.get(donwload_url)
    with open(save_filename,"wb") as f:
        f.write(r.content)
    f.close()


#==============================================
if __name__ == '__main__':
    main()