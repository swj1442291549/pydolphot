import numpy as np
import glob
import os
import sys
import subprocess
from astropy.io import fits
import pandas as pd


def extract_ref(rawdir='raw/'):
    ref_files = sorted(glob.glob("{0}/*drz.fits".format(rawdir)))
    filenames = [j.replace(rawdir, "") for j in ref_files]
    for i, j in enumerate(filenames):
        print("{0}: {1}".format(i, j))
    index = input('Use which drz file as the reference: ')
    if index.isdigit():
        index = int(index)
    else:
        raise ValueError('Please input an integer!')
    return filenames[index]


def gen_frame(ref_file, rawdir='raw/'):
    rawfiles = sorted(glob.glob(rawdir + '/*fits*'))
    if not rawfiles:
        raise IOError('No images found')
    filenames = [j.replace(rawdir, "") for j in rawfiles]
    img_names = [x for x in filenames if 'flt.' in x]
    type_list = ['image'] * len(img_names)
    img_names.append(ref_file)
    type_list.append("reference")

    df = pd.DataFrame({'img_name': img_names, 'type': type_list})

    inst_list = list()
    for i in range(len(df)):
        hdu_list = fits.open('{0}/{1}'.format(rawdir, df.iloc[i]['img_name']))
        temp = hdu_list[0].header['INSTRUME']
        inst_list.append(temp)
    df['inst'] = inst_list

    filter_list = list()
    detector_list = list()
    for i in range(len(df)):
        if df.iloc[i]['inst'] == 'ACS':
            info = acs_info('{0}/{1}'.format(rawdir, df.iloc[i]['img_name']))
            filter_list.append(info['filter'])
            detector_list.append(info['detector'])
        if df.iloc[i]['inst'] == 'WFC3':
            info = wfc3_info('{0}/{1}'.format(rawdir, df.iloc[i]['img_name']))
            filter_list.append(info['filter'])
            detector_list.append(info['detector'])
        if df.iloc[i]['inst'] == 'WFPC2':
            info = wfpc2_info('{0}/{1}'.format(rawdir, df.iloc[i]['img_name']))
            filter_list.append(info['filter'])
            detector_list.append(info['detector'])
    df['filter'] = filter_list
    df['detect'] = detector_list
    return df


def wfc3_info(filename):
    hdu_list = fits.open(filename)
    filter = hdu_list[0].header['filter']
    detector = hdu_list[0].header['DETECTOR']
    return {'filter': filter, 'detector': detector}


def acs_info(filename):
    hdu_list = fits.open(filename)
    f1 = hdu_list[0].header['filter1']
    f2 = hdu_list[0].header['filter2']
    if ((f1 == 'CLEAR1L') | (f1 == 'CLEAR1S')):
        filter = f2
    elif ((f2 == 'CLEAR2L') | (f2 == 'CLEAR2S')):
        filter = f1
    return {'filter': filter, 'detector': ''}


def load_files(df, rawdir='raw/'):
    subprocess.call("rm -rf *.fits phot[0-9].log phot[0-9].param", shell=True)
    for i in range(len(df)):
        subprocess.call(
            "cp {0}/{1} {2}".format(rawdir, df.iloc[i]["img_name"],
                                    os.getcwd()),
            shell=True)


def mask_files(df):
    for i in range(len(df)):
        if df.iloc[i]['inst'] == 'WFC3':
            subprocess.call(
                "wfc3mask " + df.iloc[i]['img_name'] + " > phot.log",
                shell=True)
        if df.iloc[i]['inst'] == 'ACS':
            subprocess.call(
                "acsmask " + df.iloc[i]['img_name'] + " > phot.log", shell=True)


def split_files(df):
    for i in range(len(df)):
        subprocess.call(
            "splitgroups " + df.iloc[i]['img_name'] + " > phot.log", shell=True)


def calsky_files(df):
    for i in range(len(df)):
        if df.iloc[i]['inst'] == 'WFC3':
            wfc3_calsky(df.iloc[i])
        if df.iloc[i]['inst'] == 'ACS':
            acs_calsky(df.iloc[i])


def wfc3_calsky(item):
    if item['type'] == 'reference':
        if item['detect'] == 'UVIS':
            subprocess.call(
                "calcsky " + item['img_name'].replace('.fits', '.chip1') +
                "  15 35 4 2.25 2.00 >> phot1.log",
                shell=True)
        else:
            subprocess.call(
                "calcsky " + item['img_name'].replace('.fits', '.chip1') +
                "  10 25 2 2.25 2.00 >> phot1.log",
                shell=True)
    else:
        if item['detect'] == 'UVIS':
            subprocess.call(
                "calcsky " + item['img_name'].replace('.fits', '.chip1') +
                "  15 35 4 2.25 2.00 >> phot1.log",
                shell=True)
            subprocess.call(
                "calcsky " + item['img_name'].replace('.fits', '.chip2') +
                "  15 35 4 2.25 2.00 >> phot2.log",
                shell=True)
        else:
            subprocess.call(
                "calcsky " + item['img_name'].replace('.fits', '.chip1') +
                "  10 25 2 2.25 2.00 >> phot1.log",
                shell=True)
            subprocess.call(
                "calcsky " + item['img_name'].replace('.fits', '.chip2') +
                "  10 25 2 2.25 2.00 >> phot2.log",
                shell=True)


def acs_calsky(item):
    if item['type'] == 'reference':
        subprocess.call(
            "calcsky " + item['img_name'].replace('.fits', '.chip1') +
            "  15 35 4 2.25 2.00 >> phot1.log",
            shell=True)
    else:
        subprocess.call(
            "calcsky " + item['img_name'].replace('.fits', '.chip1') +
            "  15 35 4 2.25 2.00 >> phot1.log",
            shell=True)
        subprocess.call(
            "calcsky " + item['img_name'].replace('.fits', '.chip2') +
            "  15 35 4 2.25 2.00 >> phot2.log",
            shell=True)


def param_files(df):
    acs_params = {
        'raper': '4',
        'rchi': '2.0',
        'rsky': '15 35',
        'rpsf': '10',
        'apsky': '15 25',
        'shift': '0 0',
        'xform': '1 0 0'
    }

    uvis_params = {
        'raper': '4',
        'rchi': '2.0',
        'rsky': '15 35',
        'rpsf': '10',
        'apsky': '15 25',
        'shift': '0 0',
        'xform': '1 0 0'
    }

    ir_params = {
        'raper': '3',
        'rchi': '1.5',
        'rsky': '8 20',
        'rpsf': '10',
        'apsky': '15 25',
        'shift': '0 0',
        'xform': '1 0 0'
    }

    dolphot_params = {
        'SkipSky': 2,
        'SkySig': 2.25,
        'SecondPass': 5,
        'SigFind': 2.5,
        'SigFindMult': 0.85,
        'SigFinal': 3.5,
        'MaxIT': 25,
        'NoiseMult': 0.1,
        'FSat': 0.999,
        'ApCor': 1,
        'RCentroid': 2,
        'PosStep': 0.25,
        'dPosMax': 2.5,
        'RCombine': 1.5,
        'SigPSF': 5.0,
        'PSFres': 1,
        'PSFPhot': 1,
        'FitSky': 1,
        'Force1': 0,
        'Align': 2,
        'Rotate': 1,
        'WFC3useCTE': 1,
        'FlagMask': 4,
        'CombineChi': 0,
        'WFC3IRpsfType': 0,
        'WFC3UVISpsfType': 0,
        'ACSuseCTE': 1,
        'ACSpsfType': 0,
        'InterpPSFlib': 1,
        'UseWCS': 1,
        'psfoff': 0.0,
        'SearchMode': 1,
        'SubResRef': 1,
        'DiagPlotType': 'PS',
        '#FakeStars': 'fake.list',
        '#FakeMatch': 3.0,
        '#FakeStarPSF': 1.5,
        '#RandomFake': 1
    }

    df_img = df[df['type'] == 'image']
    df_ref = df[df['type'] == 'reference']
    len_image = len(df_img)

    paramfile = 'phot1.param'
    with open(paramfile, 'w') as f:
        f.write("Nimg={0:d}\n".format(len_image))
        f.write("img0_file = {0}\n".format(df_ref.iloc[0]['img_name'].replace(
            '.fits', '.chip1')))
        f.write("img0_shift = 0 0\n")
        f.write("img0_xform = 1 0 0\n")
        for i in range(len(df_img)):
            f.write("img{0:d}_file = {1}\n".format(i + 1, df_img.iloc[i][
                'img_name'].replace('.fits', '.chip1')))
        f.write('\n')
        for i in range(len(df_img)):
            if df_img.iloc[i]['inst'] == 'WFC3':
                if df_img.iloc[i]['detect'] == 'UVIS':
                    params = uvis_params
                else:
                    params = ir_params
            else:
                params = acs_params
            f.write("img{0}_shift = {1}\n".format(i + 1, params['shift']))
            f.write("img{0}_xform = {1}\n".format(i + 1, params['xform']))
            f.write("img{0}_raper = {1}\n".format(i + 1, params['raper']))
            f.write("img{0}_rsky = {1}\n".format(i + 1, params['rsky']))
            f.write("img{0}_rchi = {1}\n".format(i + 1, params['rchi']))
            f.write("img{0}_rpsf = {1}\n".format(i + 1, params['rpsf']))
            f.write("img{0}_apsky = {1}\n".format(i + 1, params['apsky']))
        f.write('\n')
        if df_img.iloc[0]['inst'] == 'WFC3' and df_img.iloc[0]['detect'] != 'UVIS':
            dolphot_params['SkipSky'] = 1
        for i in dolphot_params.keys():
            f.write(i + ' = ' + np.str(dolphot_params[i]) + "\n")

    paramfile = 'phot2.param'
    with open(paramfile, 'w') as f:
        f.write("Nimg={0:d}\n".format(len_image))
        f.write("img0_file = {0}\n".format(df_ref.iloc[0]['img_name'].replace(
            '.fits', '.chip1')))
        f.write("img0_shift = 0 0\n")
        f.write("img0_xform = 1 0 0\n")
        for i in range(len(df_img)):
            f.write("img{0:d}_file = {1}\n".format(i + 1, df_img.iloc[i][
                'img_name'].replace('.fits', '.chip2')))
        f.write('\n')
        for i in range(len(df_img)):
            if df_img.iloc[i]['inst'] == 'WFC3':
                if df_img.iloc[i]['detect'] == 'UVIS':
                    params = uvis_params
                else:
                    params = ir_params
            else:
                params = acs_params
            f.write("img{0}_shift = {1}\n".format(i + 1, params['shift']))
            f.write("img{0}_xform = {1}\n".format(i + 1, params['xform']))
            f.write("img{0}_raper = {1}\n".format(i + 1, params['raper']))
            f.write("img{0}_rsky = {1}\n".format(i + 1, params['rsky']))
            f.write("img{0}_rchi = {1}\n".format(i + 1, params['rchi']))
            f.write("img{0}_rpsf = {1}\n".format(i + 1, params['rpsf']))
            f.write("img{0}_apsky = {1}\n".format(i + 1, params['apsky']))
        f.write('\n')
        if df_img.iloc[0]['inst'] == 'WFC3' and df_img.iloc[0]['detect'] != 'UVIS':
            dolphot_params['SkipSky'] = 1
        for i in dolphot_params.keys():
            f.write(i + ' = ' + np.str(dolphot_params[i]) + "\n")


if __name__ == "__main__":
    ref_file = extract_ref()
    df = gen_frame(ref_file)
    load_files(df)
    mask_files(df)
    split_files(df)
    calsky_files(df)
