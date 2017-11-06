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



def read_data(data_name, w):
    data = np.loadtxt(data_name)
    num = np.arange(len(data[:, 0])) + 1
    world = w.wcs_pix2world(data[:, 2], data[:, 3], 1)
    ra = world[0]
    dec = world[1]
    chip_num = int(data_name.split('.')[0][-1])
    chip = np.array([chip_num] * len(num))
    return {'ra': ra, 'dec': dec, 'data': data, 'chip': chip}



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

    outputname = glob.glob('fake/output*')
    data_dict = {'ra': list(), 'dec': list(), 'data': list(), 'chip': list()}
    for data_name in outputname:
        data = read_data(data_name, w)
        for key in data_dict.keys():
            data_dict[key].append(data[key])

    ra = np.concatenate(data_dict['ra'])
    dec = np.concatenate(data_dict['dec'])
    data = np.concatenate(data_dict['data'])
    chip = np.concatenate(data_dict['chip'])

    
    t = astropy.table.Table()
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
