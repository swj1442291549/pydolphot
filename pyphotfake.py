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
    t.add_column(astropy.table.Column(name='{0}_VEGA'.format(filter1),
                                      data=data[:, 5])) 
    t.add_column(astropy.table.Column(name='{0}_NUM'.format(filter2),
                                      data=data[:, 6])) 
    t.add_column(astropy.table.Column(name='{0}_VEGA'.format(filter2),
                                      data=data[:, 7])) 

    t.write('o.fake.fits', overwrite=True)

    subprocess.call('mv o.fake.fits final')
