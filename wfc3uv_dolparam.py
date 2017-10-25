from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
import glob
import os
import sys
import subprocess
import pdb
import argparse
from astropy.io import fits


# currently assumes *all* relevant fits files are in the same raw directory
def load_files(ref_file,
               rawdir='raw/',
               log_file='phot[0-9].log',
               param_file='phot[0-9].param'):
    """Copy necessary files out of rawdir

    Args:
        ref_file (string): reference file
        rawdir (string): raw file directory
                         (raw/)
        log_file (string): pattern for log files
                           (phot[0-9].log)
        param_file (string): pattern for parameter files
                             (phot[0-9].param)

    Returns:
        img_names (list): list of necessary image files
        ref_list (list): list of reference file
    """
    # remove old fits, parameter files
    subprocess.call("rm -rf *.fits " + param_file + " " + log_file, shell=True)

    rawfiles = sorted(glob.glob(rawdir + '/*fits*'))
    filenames = [j.replace(rawdir, "") for j in rawfiles]
    img_names = [x for x in filenames if 'flt.' in x]

    if not rawfiles:
        raise IOError('No images found')

    #copy images from raw into working directory
    for i in img_names:
        subprocess.call("cp " + rawdir + i + " " + os.getcwd(), shell=True)

    # copy reference files from raw into working directory
    subprocess.call("cp " + rawdir + ref_file + " " + os.getcwd(), shell=True)

    # check if they're zipped, and if so, unzip them
    if ref_file.split(".")[-1] == 'gz':
        subprocess.call("gunzip " + ref_file, shell=True)
        ref_file = ref_file.strip(".gz")
    for i, j in enumerate(img_names):
        if j.split(".")[-1] == 'gz':
            subprocess.call("gunzip " + j, shell=True)
            img_names[i] = j.strip(".gz")
    return img_names, [ref_file]


def proc_wfc3(files, log_file='phot.log', is_ref=False):
    """Process wfc3 files

    Args:
        files (list): list of files
        log_file (string): log file
                           (phot.log)
        is_ref (Boolean): is reference or not
                          (False)

    Returns:
        splitnames (dict): dictionary of chip1 and chip2
    """
    # rename files to include filter name
    newname_store = []
    f1_store = []
    f2_store = []
    for i in range(len(files)):
        hdu = fits.open(files[i])
        f1 = hdu[0].header['filter']
        name = files[i].split('_')
        filter = f1.swapcase()
        newname = name[0] + '_' + filter + '_' + name[1]
        f1_store.append(filter)
        newname_store.append(newname)
        hdu.writeto(newname, clobber=True)

    # run wfc3mask on all WFC3 files
    splitnames = {'chip1': [], 'chip2': []}
    for j in newname_store:
        subprocess.call("wfc3mask " + j + " > " + log_file, shell=True)
        subprocess.call("splitgroups " + j + " > " + log_file, shell=True)
        if is_ref == True:
            subprocess.call(
                "calcsky " + j.replace('.fits', '.chip1') +
                "  15 35 4 2.25 2.00 >> " + log_file,
                shell=True)
            splitnames['chip1'].append(j.replace('.fits', '.chip1.fits'))
        elif is_ref == False:
            subprocess.call(
                "calcsky " + j.replace('.fits', '.chip1') +
                "  15 35 4 2.25 2.00 >> " + log_file,
                shell=True)
            splitnames['chip1'].append(j.replace('.fits', '.chip1.fits'))
            subprocess.call(
                "calcsky " + j.replace('.fits', '.chip2') +
                "  15 35 4 2.25 2.00 >> " + log_file,
                shell=True)
            splitnames['chip2'].append(j.replace('.fits', '.chip2.fits'))
    return splitnames


def ref_params(ref_dict, paramfile):
    """Generate parameters for reference

    Args:
        ref_dict (dict): dict of reference file
        paramfile (string): parameter file

    """
    file = open(paramfile, 'a')
    file.write("img0_file = " + ref_dict['chip1'][0].split('.fits')[0] + "\n")
    file.write("img0_shift = " + "0 0" + "\n")
    file.write("img0_xform = " + "1 0 0" + "\n")
    file.close()


# write out DOLPHOT parameters for individual images
def image_params(images, chip, paramfile):
    """Generate parameters for iamges

    Args:
        images (dict): dict of reference file
        chip (string): chip
        paramfile (string): parameter file

    """
    params = {
        'raper': '4',
        'rchi': '2.0',
        'rsky': '15 35',
        'rpsf': '10',
        'apsky': '15 25',
        'shift': '0 0',
        'xform': '1 0 0'
    }

    file = open(paramfile, 'a')
    k = 1

    for j in images[chip]:
        file.write("img" + np.str(k) + '_file = ' + j.split('.fits')[0] + "\n")
        k += 1
    file.write("\n")
    file.close()
    file = open(paramfile, 'a')
    k = 1  # reset image counter
    for j in images[chip]:
        file.write("img" + np.str(k) + '_shift = ' + params['shift'] + "\n")
        file.write("img" + np.str(k) + '_xform = ' + params['xform'] + "\n")
        file.write("img" + np.str(k) + '_RAper = ' + params['raper'] + "\n")
        file.write("img" + np.str(k) + '_Rchi = ' + params['rchi'] + "\n")
        file.write("img" + np.str(k) + '_Rsky = ' + params['rsky'] + "\n")
        file.write("img" + np.str(k) + '_RPSF = ' + params['rpsf'] + "\n")
        file.write("img" + np.str(k) + '_apsky = ' + params['apsky'] + "\n")
        k += 1
    file.write("\n")
    file.close()


def dolparams(paramfile):
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
        'RPSF': 10,
        'SigPSF': 5.0,
        'PSFres': 1,
        'FitSky': 1,
        'Force1': 0,
        'Align': 2,
        'Rotate': 1,
        'WFC3useCTE': 1,
        'WFC3UVISpsfType': 0,
        'WFC3IRpsfType': 0,
        'FlagMask': 4,
        'CombineChi': 0,
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

    file = open(paramfile, 'a')
    for i in dolphot_params.keys():
        file.write(i + ' = ' + np.str(dolphot_params[i]) + "\n")
    file.close()


def gen_script():
    with open('run.sh', 'w') as f:
        f.write("dolphot output1 -pphot1.param >> phot1.log &\n")
        f.write("dolphot output2 -pphot2.param >> phot2.log &\n")
    subprocess.call('chmod a+x run.sh', shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ref_name", help='File name of reference file (drz)')
    args = parser.parse_args()
    ref = args.ref_name

    log_file_o = 'phot.log'
    param_file_o = 'phot.param'

    # load in HST images
    file_list, ref_list = load_files(ref)

    files_dict = proc_wfc3(file_list)
    number_images = len(files_dict['chip1'])
    ref_dict = proc_wfc3(ref_list, is_ref=True)

    # write number of images
    for i, chip in enumerate(ref_dict.keys()):
        param_file = "{0}{1}.{2}".format(
            param_file_o.split('.')[0], i + 1, param_file_o.split('.')[1])
        log_file = "{0}{1}.{2}".format(
            log_file_o.split('.')[0], i + 1, log_file_o.split('.')[1])
        file = open(param_file, 'w')
        file.write("Nimg = " + np.str(number_images) + "\n")
        file.close()

        # add reference file info
        ref_params(ref_dict, param_file)
        # start counter for image numbers
        image_params(files_dict, chip, param_file)
        # add gloal dolphot parameters
        dolparams(param_file)
