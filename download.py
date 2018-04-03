import subprocess
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('index', type=int, help='Index of anonymous')
    parser.add_argument(
        '-c', type=int, default=10, help='Number of connections (10)')
    args = parser.parse_args()
    index = args.index
    num_con = args.c
    proc = subprocess.Popen(["curl", "-l", "ftp://stdatu.stsci.edu/stage/anonymous/anonymous{0:0>5}/".format(index)], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    files = out.decode('utf8').split('\n')
    files.remove('')

    for filename in files:
        print('Downloading {0} / {1} ...'.format(files.index(filename), len(files)))
        subprocess.call("axel -a -n {2} ftp://stdatu.stsci.edu/stage/anonymous/anonymous{0:0>5}/{1}".format(index, filename, num_con), shell=True)

    subprocess.call('mkdir raw', shell=True)
    subprocess.call('mv *.fits raw', shell=True)

