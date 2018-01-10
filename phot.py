import numpy as np
import sys
import astropy.table
from astropy import units as u
from astropy.io import fits
from astropy import wcs
import pandas as pd
from collections import Counter
import subprocess
import os
import glob

if __name__ == "__main__":
    refname = glob.glob('*drz.fits')[0]

    data_1_name = 'output1'
    data_2_name = 'output2'

    global_labels = ['Number', 'RA', 'DEC', 'X', 'Y', 'OBJECT_TYPE']
    filter_labels = [
        '_VEGA', '_ERR', '_SNR', '_SHARP', '_ROUND', '_CROWD', '_FLAG'
    ]
    formats = ['f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8']

    # read filters from output1.columns
    df_column = pd.read_table('output1.columns', names=['column'])
    filters = []
    for i in range(int((len(df_column) - 11) / 13)):
        column = df_column.iloc[11 + 13 * i]['column']
        if '(' in column:
            column_filter = column.split('(')[1].split(',')[0]  # ACS
        else:
            column_filter = column.split(',')[1].strip()  # WFC3
        if column_filter not in filters:
            filters.append(column_filter)

    nfilters = len(filters)

    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)

    print('Loading raw DOLPHOT file for chip1...')
    data_1 = np.loadtxt(data_1_name)
    print('Loaded {0} objects'.format(len(data_1)))
    num_1 = np.arange(len(data_1[:, 0])) + 1
    world_1 = w.wcs_pix2world(data_1[:, 2], data_1[:, 3], 1)

    print('Loading raw DOLPHOT file for chip2...')
    data_2 = np.loadtxt(data_2_name)
    print('Loaded {0} objects'.format(len(data_2)))
    num_2 = np.arange(len(data_2[:, 0])) + len(data_1) + 1
    world_2 = w.wcs_pix2world(data_2[:, 2], data_2[:, 3], 1)

    num = np.append(num_1, num_2)
    ra = np.append(world_1[0], world_2[0])
    dec = np.append(world_1[1], world_2[1])
    data = np.concatenate((data_1, data_2), axis=0)
    chip = np.append(np.array([1] * len(num_1)), np.array([2] * len(num_2)))

    t = astropy.table.Table()
    t.add_column(astropy.table.Column(name=global_labels[0],
                                      data=num))  # star number
    t.add_column(astropy.table.Column(name='chip', data=chip))  # chip number
    t.add_column(astropy.table.Column(name=global_labels[1], data=ra))  # RA
    t.add_column(astropy.table.Column(name=global_labels[2], data=dec))  # DEC
    t.add_column(astropy.table.Column(name=global_labels[3],
                                      data=data[:, 2]))  # X
    t.add_column(astropy.table.Column(name=global_labels[4],
                                      data=data[:, 3]))  # Y
    t.add_column(astropy.table.Column(name=global_labels[5],
                                      data=data[:, 10]))  # ObjType
    cols = np.int_(np.asarray((15, 17, 19, 20, 21, 22, 23)))

    # loops over number of filters, names of filters to generate output columns
    for i in range(nfilters):
        for j, k in enumerate(filter_labels):
            t.add_column(
                astropy.table.Column(
                    name=filters[i] + k, data=data[:, cols[j] + (i * 13)]))

    t.write('o.summary.fits', overwrite=True)

    snr = 5.
    sharp = 0.04
    crowd = 0.5
    objtype = 1
    flag = 99

    wgood_list = list()
    for i in range(nfilters):
        wgood = np.where((t[filters[i] + '_SNR'] >= snr) & (
            t[filters[i] + '_SHARP']**2 < sharp
        ) & (t[filters[i] + '_CROWD'] < crowd) & (t['OBJECT_TYPE'] == objtype) &
                         (t[filters[i] + '_FLAG'] <= flag))
    cnt = Counter(np.concatenate(wgood_list))
    wgood_index = [k for k, v in cnt.items() if v >= nfilters]

    t1 = t[wgood_index]
    t1.write('o.gst.fits', overwrite=True)

    if not os.path.isdir("final"):
        subprocess.call('mkdir final', shell=True)
    subprocess.call('mv o.summary.fits final', shell=True)
    subprocess.call('mv o.gst.fits final', shell=True)
