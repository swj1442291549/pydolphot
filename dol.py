import os
import re
import sys
import glob
import argparse
import subprocess

from pathlib import Path
from collections import Counter
from tqdm import tqdm

import numpy as np
import pandas as pd

from astropy.io import fits

from multiprocessing import Pool


def extract_ref(force, rawdir="raw/"):
    """Read drz files from rawdir

    Args:
        force (boolean): force execute
        rawdir (string): raw folder
                         (raw/)

    Returns:
        filename (string): drz filename
    """
    ref_files = sorted(glob.glob("{0}/*drz.fits".format(rawdir)))
    filenames = [j.replace(rawdir, "") for j in ref_files]
    if not force:
        for i, j in enumerate(filenames):
            print("{0}: {1}".format(i, j))
        index = input("Use which drz file as the reference: ")
        if index.isdigit():
            index = int(index)
        else:
            raise ValueError("Please input an integer!")
    else:
        index = 0
    return filenames[index]


def gen_frame(ref_file, rawdir="raw/"):
    """Generating the data frame

    Args:
        ref_file (string): drz filename
        rawdir (stinrg): raw folder
                         (raw/)

    Returns:
        df (DataFrmae): data
    """
    print("Reading ...")
    rawfiles = sorted(glob.glob(rawdir + "/*fits*"))
    if not rawfiles:
        raise IOError("No images found")
    filenames = [j.replace(rawdir, "") for j in rawfiles]
    img_names = [x for x in filenames if "flt." in x or "c0m." in x]
    type_list = ["image"] * len(img_names)
    img_names.append(ref_file)
    type_list.append("reference")

    df = pd.DataFrame({"img_name": img_names, "type": type_list})

    inst_list = list()
    for i in range(len(df)):
        hdu_list = fits.open("{0}/{1}".format(rawdir, df.iloc[i]["img_name"]))
        temp = hdu_list[0].header["INSTRUME"]
        inst_list.append(temp)
    df["inst"] = inst_list

    filter_list = list()
    detector_list = list()
    exp_list = list()
    prop_list = list()
    pr_l_list = list()
    pr_f_list = list()
    for i in range(len(df)):
        if df.iloc[i]["inst"] == "ACS":
            info = acs_info("{0}/{1}".format(rawdir, df.iloc[i]["img_name"]))
        if df.iloc[i]["inst"] == "WFC3":
            info = wfc3_info("{0}/{1}".format(rawdir, df.iloc[i]["img_name"]))
        if df.iloc[i]["inst"] == "WFPC2":
            info = wfpc2_info("{0}/{1}".format(rawdir, df.iloc[i]["img_name"]))
        filter_list.append(info["filter"])
        detector_list.append(info["detector"])
        exp_list.append(info["exp"])
        prop_list.append(info["prop"])
        pr_l_list.append(info["pr_l"])
        pr_f_list.append(info["pr_f"])
    df["filter"] = filter_list
    df["detect"] = detector_list
    df["exp"] = exp_list
    df["prop"] = prop_list
    df["pr_l"] = pr_l_list
    df["pr_f"] = pr_f_list
    return df


def wfc3_info(filename):
    """get info for WFC3 instrument

    Args:
        filename (string): file name

    Returns:
        dict (dictionary): filter and detector
    """
    hdu_list = fits.open(filename)
    filter = hdu_list[0].header["filter"]
    detector = hdu_list[0].header["DETECTOR"]
    exp = hdu_list[0].header["EXPTIME"]
    prop = hdu_list[0].header["PROPOSID"]
    if "PR_INV_L" in hdu_list[0].header:
        pr_l = hdu_list[0].header["PR_INV_L"]
        pr_f = hdu_list[0].header["PR_INV_F"]
    else:
        pr_l = ""
        pr_f = ""
    return {
        "filter": filter,
        "detector": detector,
        "exp": exp,
        "prop": prop,
        "pr_l": pr_l,
        "pr_f": pr_f,
    }


def wfpc2_info(filename):
    """get info for WFPC2 instrument

    Args:
        filename (string): file name

    Returns:
        dict (dictionary): filter and detector
    """
    hdu_list = fits.open(filename)
    filter = hdu_list[0].header["FILTNAM1"]
    detector = ""
    exp = hdu_list[0].header["EXPTIME"]
    prop = hdu_list[0].header["PROPOSID"]
    if "PR_INV_L" in hdu_list[0].header:
        pr_l = hdu_list[0].header["PR_INV_L"]
        pr_f = hdu_list[0].header["PR_INV_F"]
    else:
        pr_l = ""
        pr_f = ""
    return {
        "filter": filter,
        "detector": detector,
        "exp": exp,
        "prop": prop,
        "pr_l": pr_l,
        "pr_f": pr_f,
    }


def acs_info(filename):
    """get info for ACS instrument

    Args:
        filename (string): file name

    Returns:
        dict (dictionary): filter and detector
    """
    hdu_list = fits.open(filename)
    f1 = hdu_list[0].header["filter1"]
    f2 = hdu_list[0].header["filter2"]
    if (f1 == "CLEAR1L") | (f1 == "CLEAR1S"):
        filter = f2
    elif (f2 == "CLEAR2L") | (f2 == "CLEAR2S"):
        filter = f1
    exp = hdu_list[0].header["EXPTIME"]
    detector = hdu_list[0].header["DETECTOR"]
    prop = hdu_list[0].header["PROPOSID"]
    if "PR_INV_L" in hdu_list[0].header:
        pr_l = hdu_list[0].header["PR_INV_L"]
        pr_f = hdu_list[0].header["PR_INV_F"]
    else:
        pr_l = ""
        pr_f = ""
    return {
        "filter": filter,
        "detector": detector,
        "exp": exp,
        "prop": prop,
        "pr_l": pr_l,
        "pr_f": pr_f,
    }


def load_files(df, rawdir="raw/"):
    """Clean and load the data

    Args:
        df (DataFrame): data frame
        rawdir (string): raw folder
                         (raw/)
    """
    subprocess.call("rm -rf *.fits phot[0-9].log phot[0-9].param", shell=True)
    for i in range(len(df)):
        subprocess.call(
            "cp {0}/{1} {2}".format(rawdir, df.iloc[i]["img_name"], os.getcwd()),
            shell=True,
        )
        if df.iloc[i].inst == "WFPC2":
            subprocess.call(
                "cp {0}/{1} {2}".format(
                    rawdir, re.sub("c0m", "c1m", df.iloc[i]["img_name"]), os.getcwd()
                ),
                shell=True,
            )


def mask_files(df):
    """Mask the files

    Args:
        df (DataFrame): data frame

    """
    print("Masking ...")
    for i in range(len(df)):
        if df.iloc[i]["inst"] == "WFC3":
            subprocess.call(
                "wfc3mask " + df.iloc[i]["img_name"] + " >> phot.log", shell=True
            )
        elif df.iloc[i]["inst"] == "ACS":
            subprocess.call(
                "acsmask " + df.iloc[i]["img_name"] + " >> phot.log", shell=True
            )
        elif df.iloc[i]["inst"] == "WFPC2":
            subprocess.call(
                "wfpc2mask "
                + df.iloc[i]["img_name"]
                + " "
                + re.sub("c0m", "c1m", df.iloc[i]["img_name"])
                + " >> phot.log",
                shell=True,
            )


def split_files(df):
    """split the files

    Args:
        df (DataFrame): data frame

    """
    print("Splitting ...")
    for i in range(len(df)):
        subprocess.call(
            "splitgroups " + df.iloc[i]["img_name"] + " >> phot.log", shell=True
        )


def inner_calsky(item):
    if item["inst"] == "WFC3":
        wfc3_calsky(item)
    elif item["inst"] == "ACS":
        acs_calsky(item)
    elif item["inst"] == "WFPC2":
        wfpc2_calsky(item)


def calsky_files(df):
    """calsky the files

    Args:
        df (DataFrame): data frame

    """
    print("Calculating sky ...")
    with Pool(len(df)) as p:
        with tqdm(total=len(df)) as pbar:
            for i in tqdm(
                enumerate(
                    p.imap_unordered(inner_calsky, [df.iloc[i] for i in range(len(df))])
                )
            ):
                pbar.update()


def wfc3_calsky(item):
    """Calsky parameter for WFC3

    Args:
        item (item): item
    """
    if item["type"] == "reference":
        if item["detect"] == "UVIS":
            subprocess.call(
                "calcsky "
                + item["img_name"].replace(".fits", ".chip1")
                + "  15 35 4 2.25 2.00 >> phot1.log",
                shell=True,
            )
        else:
            subprocess.call(
                "calcsky "
                + item["img_name"].replace(".fits", ".chip1")
                + "  10 25 2 2.25 2.00 >> phot1.log",
                shell=True,
            )
    else:
        if item["detect"] == "UVIS":
            subprocess.call(
                "calcsky "
                + item["img_name"].replace(".fits", ".chip1")
                + "  15 35 4 2.25 2.00 >> phot1.log",
                shell=True,
            )
            subprocess.call(
                "calcsky "
                + item["img_name"].replace(".fits", ".chip2")
                + "  15 35 4 2.25 2.00 >> phot2.log",
                shell=True,
            )
        else:
            subprocess.call(
                "calcsky "
                + item["img_name"].replace(".fits", ".chip1")
                + "  10 25 2 2.25 2.00 >> phot1.log",
                shell=True,
            )
            subprocess.call(
                "calcsky "
                + item["img_name"].replace(".fits", ".chip2")
                + "  10 25 2 2.25 2.00 >> phot2.log",
                shell=True,
            )


def acs_calsky(item):
    """Calsky parameter for ACS

    Args:
        item (item): item
    """
    if item["type"] == "reference":
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip1")
            + "  15 35 4 2.25 2.00 >> phot1.log",
            shell=True,
        )
    else:
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip1")
            + "  15 35 4 2.25 2.00 >> phot1.log",
            shell=True,
        )
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip2")
            + "  15 35 4 2.25 2.00 >> phot2.log",
            shell=True,
        )


def wfpc2_calsky(item):
    """Calsky parameter for WFPC2

    Args:
        item (item): item
    """
    if item["type"] == "reference":
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip1")
            + "  10 25 2 2.25 2.00 >> phot1.log",
            shell=True,
        )
    else:
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip1")
            + "  10 25 2 2.25 2.00 >> phot1.log",
            shell=True,
        )
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip2")
            + "  10 25 2 2.25 2.00 >> phot2.log",
            shell=True,
        )
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip3")
            + "  10 25 2 2.25 2.00 >> phot3.log",
            shell=True,
        )
        subprocess.call(
            "calcsky "
            + item["img_name"].replace(".fits", ".chip4")
            + "  10 25 2 2.25 2.00 >> phot4.log",
            shell=True,
        )


def param_files(df, chip_num):
    """Generate parameter files

    Args:
        df (DataFrame): data frame
        chip_num (int): number of chips
    """
    acs_params = {
        "raper": "3",
        "rchi": "2.0",
        "rsky": "15 35",
        "rsky2": "4 10",
        "rpsf": "13",
        "apsky": "15 25",
        "shift": "0 0",
        "xform": "1 0 0",
    }

    uvis_params = {
        "raper": "3",
        "rchi": "2.0",
        "rsky": "15 35",
        "rsky2": "4 10",
        "rpsf": "13",
        "apsky": "15 25",
        "shift": "0 0",
        "xform": "1 0 0",
    }

    ir_params = {
        "raper": "2",
        "rchi": "1.5",
        "rsky": "8 20",
        "rsky2": "3 10",
        "rpsf": "15",
        "apsky": "8 20",
        "shift": "0 0",
        "xform": "1 0 0",
    }

    wfpc2_params = {
        "raper": "3",
        "rchi": "2.0",
        "rsky": "15 35",
        "rsky2": "4 10",
        "rpsf": "15",
        "apsky": "15 25",
        "apsize": "20 50 100",
        "shift": "0 0",
        "xform": "1 0 0",
    }

    dolphot_params = {
        "SkipSky": 2,  # 1 for WFC3/IR
        "SkySig": 2.25,
        "SecondPass": 5,
        "SigFind": 2.5,
        "SigFindMult": 0.85,
        "SigFinal": 3.5,
        "MaxIT": 25,
        "NoiseMult": 0.1,
        "FSat": 0.999,
        "ApCor": 1,
        "RCentroid": 2,
        "PosStep": 0.25,
        "dPosMax": 3.0,
        "RCombine": 1.5,
        "SigPSF": 5.0,
        "PSFres": 1,
        "PSFPhot": 1,
        "PSFPhotIt": 2,
        "FitSky": 1,
        "Force1": 0,
        "Align": 2,
        "Rotate": 1,
        "WFC3useCTE": 1,
        "WFPC2useCTE": 1,
        "FlagMask": 4,
        "CombineChi": 0,
        "WFC3IRpsfType": 0,
        "WFC3UVISpsfType": 0,
        "ACSuseCTE": 1,
        "ACSpsfType": 0,
        "InterpPSFlib": 1,
        "UseWCS": 1,
        "psfoff": 0.0,
        "SearchMode": 1,
        "SubResRef": 1,
        "DiagPlotType": "PS",
    }

    df_img = df[df["type"] == "image"]
    df_ref = df[df["type"] == "reference"]
    len_img = len(df_img)

    for chip in range(1, 1 + chip_num):
        paramfile = "phot{0:d}.param".format(chip)
        with open(paramfile, "w") as f:
            f.write("Nimg={0:d}\n".format(len_img))
            f.write(
                "img0_file={0}\n".format(
                    df_ref.iloc[0]["img_name"].replace(".fits", ".chip1")
                )
            )
            f.write("img0_shift=0 0\n")
            f.write("img0_xform=1 0 0\n")
            for i in range(len_img):
                img_number = i + 1
                f.write(
                    "img{0:d}_file = {1}\n".format(
                        img_number,
                        df_img.iloc[i]["img_name"].replace(
                            ".fits", ".chip{0:d}".format(chip)
                        ),
                    )
                )
                if df_img.iloc[i]["inst"] == "WFC3":
                    if df_img.iloc[i]["detect"] == "UVIS":
                        params = uvis_params
                    else:
                        params = ir_params
                elif df_img.iloc[i]["inst"] == "ACS":
                    params = acs_params
                elif df_img.iloc[i]["inst"] == "WFPC2":
                    params = wfpc2_params
                f.write("img{0}_shift={1}\n".format(img_number, params["shift"]))
                f.write("img{0}_xform={1}\n".format(img_number, params["xform"]))
                f.write("img{0}_raper={1}\n".format(img_number, params["raper"]))
                f.write("img{0}_rsky={1}\n".format(img_number, params["rsky"]))
                f.write("img{0}_rchi={1}\n".format(img_number, params["rchi"]))
                f.write("img{0}_rpsf={1}\n".format(img_number, params["rpsf"]))
                f.write("img{0}_apsky={1}\n".format(img_number, params["apsky"]))
            if df_img.iloc[0]["inst"] == "WFC3" and df_img.iloc[0]["detect"] != "UVIS":
                dolphot_params["SkipSky"] = 1
            for i in dolphot_params.keys():
                f.write(i + " = " + str(dolphot_params[i]) + "\n")


def check_chip_num(df):
    df_img = df[df["type"] == "image"]
    chip_num = len(
        glob.glob("{0}.chip[1-4].fits".format(df_img.iloc[0]["img_name"].split(".")[0]))
    )
    return chip_num


def prepare_dir():
    """Prepare the directory

    Check the existence of raw. If not, move STScI into raw.
    """
    rawdir = Path("raw/")
    if rawdir.is_dir():
        print("Find raw directory.")
    else:
        print("No raw directory is found.")
        if Path("stdatu.stsci.edu").is_dir():
            print("Find STScI directory.")
            ano_dir = glob.glob("stdatu.stsci.edu/stage/anonymous/anonymous*")
            if len(ano_dir) != 1:
                print("Wring anonymous folder!")
            else:
                subprocess.call("mv -f {0} raw".format(ano_dir[0]), shell=True)
                subprocess.call("rm -rf stdatu.stsci.edu", shell=True)
                print("Complete directory preperation")


def inner_dol(chip):
    subprocess.call(
        ["dolphot", "output{0:d}".format(chip), "-pphot{0}.param".format(chip)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_dol(chip_num):
    print("Running dolphot ...")
    with Pool(chip_num) as p:
        with tqdm(total=chip_num) as pbar:
            for i in tqdm(
                enumerate(p.imap_unordered(inner_dol, range(1, chip_num + 1)))
            ):
                pbar.update()


def print_info(df):
    """Print the basic information of the data
    
    Args:
        df (DataFrame): observation data

    """
    print("ID: {0}".format(df.iloc[0]["prop"]))
    print("Camera: {0}/{1}".format(df.iloc[0]["inst"], df.iloc[0]["detect"]))
    try:
        print("PI: {0}. {1}".format(df.iloc[0]["pr_f"][0], df.iloc[0]["pr_l"]))
    except:
        print("No PI info is found")
    df_img = df[df["type"] == "image"]
    filters = Counter(df_img["filter"]).keys()
    for filter in filters:
        df_sel = df_img[df_img["filter"] == filter]
        string = "{0}: ".format(filter)
        for exp in sorted(df_sel.exp):
            string += " {0} ".format(exp)
        print(string)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--info", action="store_true", help="Print info (False)")
    parser.add_argument("--force", action="store_true", help="Force (False)")
    args = parser.parse_args()
    force = args.force
    info = args.info

    if info:
        ref_file = glob.glob("*drz.fits")[0]
        df = gen_frame(ref_file)
        print_info(df)

    else:
        prepare_dir()
        ref_file = extract_ref(force)
        df = gen_frame(ref_file)
        load_files(df)
        mask_files(df)
        split_files(df)
        chip_num = check_chip_num(df)
        calsky_files(df)
        param_files(df, chip_num)
        run_dol(chip_num)
