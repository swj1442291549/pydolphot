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
import pandas as pd
import pickle



def read_data():
    hdu_list = fits.open('final/o.gst.fits')
    data = hdu_list[1].data
    df = pd.DataFrame(np.array(data).byteswap().newbyteorder())
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Bfilter", help='Blue Filter name')
    parser.add_argument("Rfilter", help='Red Filter name')
    parser.add_argument("Num", type=int, help='Number')
    args = parser.parse_args()
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num = args.Num

    refname = glob.glob('*drz.fits')[0]
    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)


    df = read_data()
    complete_dict = dict()
    for file_name in glob.glob('complete/output*'):
        chip_num = int(file_name.split('.')[0][-1])
        fake_num = int(file_name.split('_')[0][-4:])
        if len(np.loadtxt(file_name)) > 1:
            if fake_num in complete_dict.keys():
                complete_dict[fake_num] += 1
            else:
                complete_dict[fake_num] = 1

    for key in complete_dict.keys():
        complete_dict[key] = complete_dict[key] / num

    pickle.dump(complete_dict, 'final/completeness')



