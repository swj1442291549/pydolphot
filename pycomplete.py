import subprocess
import os
import pandas as pd
import numpy as np
from astropy.io import fits
import argparse
import glob
from scipy import integrate
import random
from scipy.interpolate import interp1d
from astropy import wcs
import pickle


def generate_fake_data(num):
    hdu_list = fits.open('final/o.gst.fits')
    data = hdu_list[1].data
    df = pd.DataFrame(np.array(data).byteswap().newbyteorder())
    df = pickle.load(open('rg.pickle', 'rb'))
    ra_rand = list()
    dec_rand = list()
    for i in range(len(df)):
        r = 4 * np.pi / 180 / 3600 * np.random.random(num)
        theta = 2 * np.pi * np.random.random(num)
        item = df.iloc[i]
        ra = item['RA'] + r * np.cos(theta)
        dec = item['DEC'] + r * np.sin(theta)
        ra_rand.append(ra)
        dec_rand.append(dec)
    df = df.assign(RA_rand=ra_rand)
    df = df.assign(DEC_rand=dec_rand)
    return df
    

def generate_fakelist(item, num, w, filter1, filter2):
    chip_num = item.chip
    fake_num = item.name
    for i in range(num):
        with open('complete/fake{0}.list{1:0>4}_{2:0>3}'.format(chip_num, fake_num, i), 'w') as f:
            X, Y = w.wcs_world2pix(item['RA_rand'][i], item['DEC_rand'][i], 1)
            f.write('0 1 {0} {1} {2} {3}\n'.format(X, Y, item["{0}_VEGA".format(filter1)], item['{0}_VEGA'.format(filter2)]))


def generate_fake_param(chip_num):
    subprocess.call(
        'cp phot{0}.param phot{0}.fake.param'.format(chip_num), shell=True)
    with open('phot{0}.fake.param'.format(chip_num), 'a') as f:
        f.write("RandomFake=1\n")
        f.write("FakeMatch=3.0\n")


def run_script():
    subprocess.call('chmod a+x run_complete.sh', shell=True)
    print('Running dolphot ...')
    subprocess.call('./run_complete.sh', shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("Bfilter", help='Blue Filter name (first)')
    parser.add_argument("Rfilter", help='Red Filter name (second)')
    parser.add_argument(
        '-n', type=int, default=10, help='Number of fake stars')
    args = parser.parse_args()
    filter1 = args.Bfilter
    filter2 = args.Rfilter
    num = args.n

    if os.path.isdir('complete'):
        subprocess.call('rm -rf complete', shell=True)
    subprocess.call('mkdir complete', shell=True)

    df = generate_fake_data(num)

    generate_fake_param(1)
    generate_fake_param(2)


    refname = glob.glob('*drz.fits')[0]
    hdu_list = fits.open(refname)
    w = wcs.WCS(hdu_list[1].header)

    print('Generating fake star ...')
    for i in range(len(df)):
        item = df.iloc[i]
        generate_fakelist(item, num, w, filter1, filter2)

    
    with open('run_complete.sh', 'w') as f:
        fake_list = glob.glob('complete/fake*')
        for i in range(len(fake_list)):
            file_name = fake_list[i]
            chip_num = file_name.split('.')[0][-1]
            if i % 15 == 14:
                f.write("dolphot output{0} -pphot{0}.fake.param FakeStars={1} FakeOut={2} >> fake{0}.log\n".format(chip_num, file_name, file_name.replace('fake', 'output')))
            else:
                f.write("dolphot output{0} -pphot{0}.fake.param FakeStars={1} FakeOut={2} >> fake{0}.log&\n".format(chip_num, file_name, file_name.replace('fake', 'output')))

    run_script()
