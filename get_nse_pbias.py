#!/usr/bin/env python
'''this script calculates the nse and pbias for several channels in a SWAT+ hydrological model (rev 60.5)
        at monthly time step - intended for large scale hydrological modelling. 
            However, can be adopted for daily timestep as well.

Author  : albert nkwasa
Contact : albert.nkwasa@vub.be / nkwasa.albert@gmail.com
Date    : 2021.07.29

'''
import os
import gdal
import pandas as pd
import datetime
import sys
import warnings

warnings.filterwarnings("ignore")

# set working directory
working_dir = "# path to a working directory e.g swat+ project folder"
os.chdir(working_dir)
try:
    os.makedirs("flow_eval")
except:
    pass
os.chdir(working_dir + "\\flow_eval")


path_to_obs = "# path to observation file. for no data, please keep blank. FORMAT of the csv: 'date','flow'"
path_to_sim = "# path to the simulated file e.g channel_mon_sdmorph.csv"

path_to_lookup = "# path to channel-gauge station lookup file. FORMAT of the csv: 'channel,'station'"
cha_lookup = pd.read_csv(path_to_lookup)
cha_dic = cha_lookup.set_index('station').T.to_dict('list')


for k in os.listdir(path_to_obs):
    os.chdir(path_to_obs)
    if k.endswith('.csv'):
        file_name = k.split()[-1].split('.')[0]
        for j in cha_dic:
            if j == file_name:
                cha_id = int(cha_dic[j][0])
                obs = pd.read_csv(k)
                obs['date'] = pd.DatetimeIndex(obs['date'])
                obs_list = obs['flow'].to_list()

                start_date = obs['date'].iloc[0]
                end_date = obs['date'].iloc[-1]

                name_header = ['jday', 'mon', 'day', 'yr', 'unit', 'gis_id', 'name', 'flow_in', 'aqu_in', 'flo_out',
                               'peakr', 'sed_in', 'sed_out', 'washld', 'bedld', 'dep', 'deg_btm_in', 'deg_bank_in',
                               'hc_sed', 'width', 'depth', 'slope', 'deg_btm', 'deg_bank', 'hc_len', 'flo_in_mm', 'aqu_out', 'flo_out_mm']
                sim = pd.read_csv(path_to_sim, names=name_header, skiprows=3)
                sim = sim.drop(['jday', 'unit', 'name', 'flow_in', 'aqu_in', 'peakr', 'sed_in', 'sed_out', 'washld',
                                'bedld', 'dep', 'deg_btm_in', 'deg_bank_in', 'hc_sed', 'width', 'depth', 'slope', 'deg_btm',
                                'deg_bank', 'hc_len', 'flo_in_mm', 'aqu_out', 'flo_out_mm'], axis=1)

                sim['date'] = sim['mon'].map(str) + '-' + \
                    sim['day'].map(str) + '-' + sim['yr'].map(str)
                sim = sim.drop(['mon', 'day', 'yr'], axis=1)
                sim['date'] = pd.DatetimeIndex(sim['date'])
                sim_cha_id = sim[sim['gis_id'] == cha_id]

                mask = (sim_cha_id['date'] >= start_date) & (
                    sim_cha_id['date'] <= end_date)
                filtered = sim_cha_id.loc[mask]
                filtered['flo_obs'] = obs_list
                filtered = filtered.drop(['gis_id'], axis=1)
                filtered = filtered.set_index('date')

                # NSE calculation
                mean_obs = filtered['flo_obs'].mean()

                filtered['obs-sim'] = (filtered['flo_obs'] -
                                       filtered['flo_out'])**2
                filtered['obs-obsmean'] = (filtered['flo_obs'] - mean_obs)**2
                nse = 1 - (filtered['obs-sim'].sum() /
                           filtered['obs-obsmean'].sum())

                # PBIAS calculation
                filtered['obs-sim_pbias'] = filtered['flo_obs'] - \
                    filtered['flo_out']
                pbias = (filtered['obs-sim_pbias'].sum() /
                         filtered['flo_obs'].sum())*100

                # writing NSE and PBIAS
                filtered = filtered.drop(
                    ['obs-sim', 'obs-obsmean', 'obs-sim_pbias'], axis=1)
                filtered['nse'] = ' '
                filtered.loc[filtered.index[0], 'nse'] = nse
                filtered['pbias'] = ' '
                filtered.loc[filtered.index[0], 'pbias'] = pbias
                os.chdir(working_dir + "\\flow_eval")
                filtered.to_csv('{}_nse_pbias.csv'.format(file_name), sep=',')


print('\t > Finished')
