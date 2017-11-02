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
    parser.add_argument("filter", help='Filter name (max 2)')
    parser.add_argument("-f", '--fake', action='store_true', help='Fake star?')

    args = parser.parse_args()
    filter = args.filter
    is_fake = args.fake

    refname = glob.glob('*drz.fits')[0]
    
    if is_fake:
        outname = 'o.fake'
        data_1_name = 'output1.fake'
        data_2_name = 'output2.fake'
    else:
        outname = 'o'
        data_1_name = 'output1'
        data_2_name = 'output2'

    global_labels = ['Number', 'RA', 'DEC', 'X', 'Y', 'OBJECT_TYPE']
    filter_labels = [
        '_VEGA', '_ERR', '_SNR', '_SHARP', '_ROUND', '_CROWD', '_FLAG'
    ]
    formats = ['f8', 'f8', 'f8', 'f8', 'f8', 'f8', 'f8']

    filters = filter.split()
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
    t.add_column(astropy.table.Column(name='chip',
                                      data=chip))  # chip number
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

    t.write(outname + '.summary.fits', overwrite=True)

    snr = 5.
    sharp = 0.04
    crowd = 0.5
    objtype = 1
    flag = 1

    wgood = np.where(
        (t[filters[0] + '_SNR'] >= snr) & (t[filters[1] + '_SNR'] >= snr) &
        (t[filters[0] + '_SHARP']**2 <
         sharp) & (t[filters[1] + '_SHARP']**2 <
                   sharp) & (t[filters[0] + '_CROWD'] < crowd) &
        (t[filters[1] + '_CROWD'] < crowd) & (t['OBJECT_TYPE'] == objtype) &
        (t[filters[0] + '_FLAG'] <= flag) & (t[filters[1] + '_FLAG'] <= flag))

    t1 = t[wgood]
    t1.write(outname + '.gst.fits', overwrite=True)

    if os.path.isdir("final"):
        subprocess.call('rm -rf final', shell=True)
    subprocess.call('mkdir final', shell=True)
    subprocess.call('mv {0}.summary.fits final'.format(outname), shell=True)
    subprocess.call('mv {0}.gst.fits final'.format(outname), shell=True)
