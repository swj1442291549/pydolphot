import os
import argparse
import subprocess
import ftplib


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int, help="Index of anonymous")
    args = parser.parse_args()

    ftps = ftplib.FTP_TLS('archive.stsci.edu')
    ftps.login(user="anonymous", passwd="mail")
    ftps.prot_p() # This is a really good idea :)
    ftps.cwd('stage')
    ftps.cwd('anonymous/anonymous{0:0>d}'.format(args.index)) # stagedir is something like 'anonymous/anonyumous12345'

    filenames = ftps.nlst()
    for filename in filenames:
        print("getting " + filename)
        with open(filename, 'wb') as fp: 
            ftps.retrbinary('RETR {}'.format(filename), fp.write)

    subprocess.call("mkdir raw", shell=True)
    subprocess.call("mv *.fits raw", shell=True)
