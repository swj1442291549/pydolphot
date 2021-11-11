import os
import argparse
import subprocess
import ftplib


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int, help="Index of anonymous")
    parser.add_argument("--user", type=str, help="username")
    parser.add_argument("--passwd", type=str, help="passwd")
    args = parser.parse_args()
    index = args.index
    user = args.user
    passwd = args.passwd
    if user is None:
        user = "anonymous"
    if passwd is None:
        passwd = "email"

    ftps = ftplib.FTP_TLS('archive.stsci.edu')
    ftps.login(user=user, passwd=passwd)
    ftps.prot_p() # This is a really good idea :)
    ftps.cwd('stage')
    ftps.cwd('anonymous/anonymous{0:0>d}'.format(index)) # stagedir is something like 'anonymous/anonyumous12345'

    filenames = ftps.nlst()
    for filename in filenames:
        print("getting " + filename)
        with open(filename, 'wb') as fp: 
            ftps.retrbinary('RETR {}'.format(filename), fp.write)

    subprocess.call("mkdir raw", shell=True)
    subprocess.call("mv *.fits raw", shell=True)
