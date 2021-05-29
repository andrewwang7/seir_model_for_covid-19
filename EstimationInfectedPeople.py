import sys
import csv
import numpy as np
import pandas as pd
from scipy.integrate import odeint
from scipy.optimize import minimize
from sklearn.metrics import mean_squared_log_error, mean_squared_error
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random
from datetime import datetime as dt
import datetime
from decimal import Decimal, ROUND_HALF_UP
import re
import os

# ref: https://www.kaggle.com/yamashin/estimation-of-infection-with-seir/output
class EstimationInfectedPeople():
    def __init__(self, name, population, pd_covid_19, latent_period=5.5, ratio_population_list=[0.01], optim_days=None, optim_weight_en=1):
        # latent_period=5.1 ref: https://www.ncbi.nlm.nih.gov/pubmed/32150748
        #  The median incubation period was estimated to be 5.1 days (95% CI, 4.5 to 5.8 days)
        self.name = name.strip('*')
        self.population = population

        self.pd_covid_19 = pd_covid_19
        self.timestamp = pd_covid_19.index
        self.deaths = pd_covid_19.deaths
        self.recovered = pd_covid_19.recovered
        self.confirmed = pd_covid_19.confirmed

        if(np.isnan(self.confirmed[-1])):
            self.timestamp =  self.timestamp[:-1]
            self.deaths = self.deaths[:-1]
            self.recovered = self.recovered[:-1]
            self.confirmed = self.confirmed[:-1]

        self.deaths = self.complement_value(self.deaths)
        self.recovered = self.complement_value(self.recovered)
        self.confirmed = self.complement_value(self.confirmed)
        self.infected  = self.confirmed - self.deaths - self.recovered
        self.infected[self.infected<0] = 0

        self.estimation_confirmed = []
        self.delta_deaths_divided_by_infected = []
        self.delta_recovered_divided_by_infected = []

        #-----------------------------
        #
        idx_confirmed_start = 0
        for idx, i_confirmed in enumerate(self.confirmed):
            if(i_confirmed>=1):
                idx_confirmed_start = idx
                break

        self.timestamp = self.timestamp[idx_confirmed_start:]
        self.infected = self.infected[idx_confirmed_start:]
        self.deaths = self.deaths[idx_confirmed_start:]
        self.recovered = self.recovered[idx_confirmed_start:]
        self.confirmed = self.confirmed[idx_confirmed_start:]

        pre_deaths = 0
        pre_recovered = 0
        pre_infected = 0
        for idx, (i_recovered, i_deaths) in enumerate(zip(self.recovered, self.deaths)):
            if pre_infected != 0:
                self.delta_deaths_divided_by_infected.append((i_deaths - pre_deaths) / pre_infected)
                self.delta_recovered_divided_by_infected.append((i_recovered - pre_recovered) / pre_infected)
            else:
                self.delta_deaths_divided_by_infected.append(0)
                self.delta_recovered_divided_by_infected.append(0)

            pre_deaths = self.deaths[idx]
            pre_recovered = self.recovered[idx]
            pre_infected = self.infected[idx]
        # end of modify by andrew

        self.max = len(self.timestamp)
        self.dt = 1 #0.01
        self.time = np.arange(0, self.max, self.dt)
        self.latent_period = latent_period
        self.ratio_population_list = ratio_population_list
        self.optim_days = optim_days
        self.optim_weight_en = optim_weight_en

        self.mortality_rate = sum(self.delta_deaths_divided_by_infected) / len(self.delta_deaths_divided_by_infected)
        self.recovery_rate = sum(self.delta_recovered_divided_by_infected) / len(self.delta_recovered_divided_by_infected)

        recovery_rate_min = 0.005
        if(self.recovery_rate<recovery_rate_min):
            self.recovery_rate = recovery_rate_min

        print('self.mortality_rate', self.mortality_rate)
        print('self.recovery_rate', self.recovery_rate)

    def complement_value(self, value_list):
        pre_value_list = 0
        for idx, i_value_list in enumerate(value_list):
            if(idx>0):
                if(i_value_list<pre_value_list):
                    value_list[idx] = pre_value_list
            pre_value_list = value_list[idx]

        return value_list

    def SEIR(self, vec, time, Beta):
        # vec[0]: S:Susceptible
        # vec[1]: E:Exposed
        # vec[2]: I:Infected
        # vec[3]: R:Recovered
        # vec[4]: D:Died
        #
        # Beta:Transfer coefficient
        # Kappa:Transition rate（E to I）
        # Gamma:recovery rate
        # Tau:mortality rate
        S = vec[0]
        E = vec[1]
        I = vec[2]
        R = vec[3]
        D = vec[4]
        N = S + E + I + R + D
        Kappa = 1 / self.latent_period
        Gamma = self.recovery_rate
        Tau = self.mortality_rate
        return [-Beta * S * I / N, Beta * S * I / N - Kappa * E, Kappa * E - Gamma * I - Tau * I, Gamma * I, Tau * I]

    def estimate(self, Beta):
        vec = odeint(self.SEIR, self.initParams, self.time, args=(Beta,))
        est = vec[0:int(self.max / self.dt):int(1 / self.dt)]
        return est

    def estimate4plot(self, Beta):
        multiple = 6
        v = odeint(self.SEIR, self.bestInitParams, np.arange(0, self.max * multiple, self.dt), args=(Beta,))
        est = v[0:int(self.max * multiple / self.dt):int(1 / self.dt)]
        return est

    def func(self, params):
        est_i = self.estimate(params[0])
        '''
        log_est_i = np.log(est_i[:, 2])
        #log_est_i[log_est_i==float("-inf")] = -32  # avoid too small  # Andrew add
        #log_est_i[log_est_i <-32] = -32  # avoid too small  # Andrew add
        return np.sum(est_i[:, 2] - self.infected * log_est_i)
        '''
        # Andrew modified
        #  (S, E, I, R, D)
        # self.infected[-optim_days:,]
        # self.recovered[-optim_days:,]
        # self.deaths[-optim_days:,]
        # estimation_confirmed = (np.asarray(estimation_infection) + np.asarray(estimation_recovered) + np.asarray(estimation_deaths)).tolist()

        if (self.optim_days is None):
            optim_days = len(self.infected)
        else:
            optim_days = self.optim_days   # Days to optimise for
            if(optim_days>len(self.infected)):
                optim_days = len(self.infected)



        if(self.optim_weight_en==1):
            weights = 1 / np.arange(1, optim_days + 1)[::-1]  # Recent data is more heavily weighted
            msle_infected = mean_squared_log_error(self.infected[-optim_days:,], est_i[-optim_days:, 2], weights)
            #msle_recovered = mean_squared_log_error(self.recovered[-optim_days:, ], est_i[-optim_days:, 3], weights)
            #msle_deaths = mean_squared_log_error(self.deaths[-optim_days:, ], est_i[-optim_days:, 4], weights)
        else:
            msle_infected = mean_squared_log_error(self.infected[-optim_days:,], est_i[-optim_days:, 2], )
            #msle_recovered = mean_squared_log_error(self.recovered, est_i[:, 3], )
            #msle_deaths = mean_squared_log_error(self.deaths, est_i[:, 4], )

        #return msle_infected + msle_recovered + msle_deaths
        return msle_infected



    def getRandLP(self):
        a = random.normalvariate(self.lp, 5)
        if a < 0:
            a *= -1
        return self.lp

    def getEstimatedParams(self):
        no_new_record_cnt = 0
        max_fun = float("-inf")  # Andrew add
        bounds = [(0, None)]
        initParams = [0.001]
        step = int(self.confirmed[len(self.confirmed) - 1] / 10)
        #step = 100
        self.bestEstimatedParams = None  # Andrew add
        for ratio_population in self.ratio_population_list:
            print(f'ratio_population: {ratio_population}')
            for susceptible in range(int(self.confirmed[len(self.confirmed) - 1]), int(self.population*ratio_population), step):  # support max N self.population*0.5)
                self.initParams = [susceptible, 0, np.min(self.confirmed), 0, 0]
                estimatedParams = minimize(self.func, initParams, method="L-BFGS-B", bounds=bounds)
                if estimatedParams.success == True:
                    if max_fun < -estimatedParams.fun:
                        no_new_record_cnt = 0
                        max_fun = -estimatedParams.fun
                        #best_population = population
                        self.bestEstimatedParams = estimatedParams
                        self.bestInitParams = self.initParams
                    else:
                        no_new_record_cnt += 1
                        if no_new_record_cnt > 250:  #250#
                            print('Susceptible:', susceptible, ' Score:', max_fun)
                            break

        return self.bestEstimatedParams

    def plot(self, ax, estimatedParams):
        self.plot_bar(ax)
        self.plot_estimation(ax, estimatedParams)

        ax.set_xlabel('Date', fontsize=20)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.set_title(self.name, fontsize=25)
        ax.grid()

    def plot_bar(self, ax):
        width = 0.5
        for day, infected, recovered, deaths in zip(self.timestamp, self.infected, self.recovered, self.deaths):
            bottom = 0
            ax.bar(day, infected, width, bottom, color='red', label='Infectious')
            bottom += infected
            ax.bar(day, recovered, width, bottom, color='blue', label='Recovered')
            bottom += recovered
            ax.bar(day, deaths, width, bottom, color='black', label='Deaths')
            bottom += deaths

        ax.set_ylabel('Confirmed infections', fontsize=20)
        handler, label = ax.get_legend_handles_labels()
        ax.legend(handler[0:3], label[0:3], loc="upper left", borderaxespad=0., fontsize=20)

        return

    def plot_estimation(self, ax, estimatedParams):
        ##--------------------------------
        # estimation_infection
        day = self.timestamp[0]
        day_list = []
        max = float("-inf")
        estimated_value_list = []
        for estimated_value in self.estimate4plot(estimatedParams.x[0])[:, 2]:
            if max < estimated_value:
                max = estimated_value
                peak = (day, estimated_value)

            day_list.append(day)
            estimated_value_list.append(estimated_value)
            day += datetime.timedelta(days=1)
            if estimated_value < 0:
                break
        ax.annotate(peak[0].strftime('%Y/%m/%d') + ' ' + str(int(peak[1])), xy=peak, size=20, color="black")
        ax.plot(day_list, estimated_value_list, color='red', label="Estimation infection", linewidth=3.0)
        estimation_infection = estimated_value_list

        # --------------------------------
        # estimation_recovered
        day = self.timestamp[0]
        day_list = []
        estimated_value_list = []
        for estimated_value in self.estimate4plot(estimatedParams.x[0])[:, 3]:
            day_list.append(day)
            estimated_value_list.append(estimated_value)
            day += datetime.timedelta(days=1)
            if estimated_value < 0:
                break
        ax.plot(day_list, estimated_value_list, color='blue', label="Estimation recovered", linewidth=3.0)
        estimation_recovered = estimated_value_list

        # --------------------------------
        # estimation_deaths
        day = self.timestamp[0]
        day_list = []
        estimated_value_list = []
        for estimated_value in self.estimate4plot(estimatedParams.x[0])[:, 4]:
            day_list.append(day)
            estimated_value_list.append(estimated_value)
            day += datetime.timedelta(days=1)
            if estimated_value < 0:
                break
        ax.plot(day_list, estimated_value_list, color='black', label="Estimation deaths", linewidth=3.0)
        self.estimation_deaths = np.asarray(estimated_value_list)

        #--------------------------------
        self.estimation_confirmed = (np.asarray(estimation_infection) + np.asarray(estimation_recovered) + np.asarray(self.estimation_deaths)).tolist()

        estimation_deaths_series = pd.Series(self.estimation_deaths, index=day_list, name='estimation_deaths')
        estimation_confirmed_series = pd.Series(self.estimation_confirmed, index =day_list, name='estimation_confirmed')
        self.pd_covid_19 = pd.concat([self.pd_covid_19, estimation_confirmed_series, estimation_deaths_series], axis=1)


        max_estimation_confirmed = int(np.max(np.asarray(self.estimation_confirmed)))
        xy_show_max_estimation_confirmed = (day_list[ int(len(day_list)/2) ], max_estimation_confirmed)
        ax.annotate('max: ' + str(max_estimation_confirmed), xy=xy_show_max_estimation_confirmed, size=20, color="black")
        ax.plot(day_list, self.estimation_confirmed, color='green', label="Estimation confirmed", linewidth=3.0)

        ax.set_ylim(0, )

        handler, label = ax.get_legend_handles_labels()
        ax.legend(handler[0:7], label[0:7], loc="upper right", borderaxespad=0., fontsize=20)

        return



    def print_estimation(self, estimatedParams):
        Beta = estimatedParams.x[0]     # ->E
        Kappa = 1 / self.latent_period  # E->I
        Gamma = self.recovery_rate      # I->R
        Tau = self.mortality_rate       # I->D
        print('<<' + self.name + '>>')
        print('Beta:', Decimal(Beta).quantize(Decimal('.000000'), rounding=ROUND_HALF_UP))
        print('Kappa:', Decimal(Kappa).quantize(Decimal('.000000'), rounding=ROUND_HALF_UP))
        print('Gamma:', Decimal(Gamma).quantize(Decimal('.000000'), rounding=ROUND_HALF_UP))
        print('Tau:', Decimal(Tau).quantize(Decimal('.000000'), rounding=ROUND_HALF_UP))

        R0 = (Kappa / (Tau + Kappa)) * (Beta / (Tau + Gamma))
        print('R0:', Decimal(R0).quantize(Decimal('.000000'), rounding=ROUND_HALF_UP))


    def plot_(self):
        new_case = self.confire.diff
        self.estimation_confirmed = []


    def save_plot(self, title='', result_path=None):
        output = self.name  + '_' + title + '.png'
        if result_path is None:
            plt.savefig(output)
        else:
            plt.savefig(os.path.join(result_path, output))

