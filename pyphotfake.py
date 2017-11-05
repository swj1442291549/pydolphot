import numpy as np
import sys
import astropy.table
from astropy import units as u
from astropy.io import fits
from astropy import wcs
import argparse
import subprocess
import os
import glob


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Bfilter", help='Blue Filter name')
    parser.add_argument("Rfilter", help='Red Filter name')
    args = parser.parse_args()
    filter1 = args.Bfilter
    filter2 = args.Rfilter

    refname = glob.glob('*drz.fits')[0]
    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)

    data_1_name = 'output1.fake'
    data_2_name = 'output2.fake'

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
    t.add_column(astropy.table.Column(name='Number',
                                      data=num))  # star number
    t.add_column(astropy.table.Column(name='chip',
                                      data=chip))  # chip number
    t.add_column(astropy.table.Column(name='RA', data=ra))  # RA
    t.add_column(astropy.table.Column(name='DEC', data=dec))  # DEC
    t.add_column(astropy.table.Column(name='X',
                                      data=data[:, 2]))  # X
    t.add_column(astropy.table.Column(name='Y',
                                      data=data[:, 3]))  # Y
    t.add_column(astropy.table.Column(name='{0}_NUM'.format(filter1),
                                      data=data[:, 4])) 
    t.add_column(astropy.table.Column(name='{0}_VEGA_IN'.format(filter1),
                                      data=data[:, 5])) 
    t.add_column(astropy.table.Column(name='{0}_NUM'.format(filter2),
                                      data=data[:, 6])) 
    t.add_column(astropy.table.Column(name='{0}_VEGA_IN'.format(filter2),
                                      data=data[:, 7])) 

    filter_labels = ['_VEGA', '_ERR', '_SNR', '_SHARP', '_ROUND', '_CROWD', '_FLAG']
    cols = np.int_(np.asarray((31, 33, 35, 36, 37, 38, 39)))
    for j, k in enumerate(filter_labels):
        t.add_column(astropy.table.Column(name=filter1 + k, data=data[:, cols[j]]))
        t.add_column(astropy.table.Column(name=filter2 + k, data=data[:, cols[j] + 13]))

    t.write('o.fake.summary.fits', overwrite=True)

    snr = 5.
    sharp = 0.04
    crowd = 0.5
    objtype = 1
    flag = 1

    wgood = np.where(
        (t[filter1 + '_SNR'] >= snr) & (t[filter2 + '_SNR'] >= snr) &
        (t[filter1 + '_SHARP']**2 <
         sharp) & (t[filter2 + '_SHARP']**2 <
                   sharp) & (t[filter1 + '_CROWD'] < crowd) &
        (t[filter2 + '_CROWD'] < crowd) &
        (t[filter1 + '_FLAG'] <= flag) & (t[filter2 + '_FLAG'] <= flag))

    t1 = t[wgood]
    t1.write('o.fake.gst.fits', overwrite=True)

    if not os.path.isdir("final"):
        subprocess.call('mkdir final', shell=True)
    subprocess.call('mv o.fake.summary.fits final', shell=True)
    subprocess.call('mv o.fake.gst.fits final', shell=True)
