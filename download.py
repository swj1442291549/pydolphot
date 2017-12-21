import subprocess
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('index', type=int, help='Index of anonymous')
    args = parser.parse_args()
    index = args.index
    proc = subprocess.Popen(["curl", "-l", "ftp://stdatu.stsci.edu/stage/anonymous/anonymous{0}/".format(index)], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    files = out.decode('utf8').split('\n')
    files.remove('')

    for filename in files:
        print('Downloading {0} / {1} ...'.format(files.index(filename), len(files)))
        subprocess.call("axel -a ftp://stdatu.stsci.edu/stage/anonymous/anonymous{0}/{1}".format(index, filename), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    subprocess.call('mkdir raw', shell=True)
    subprocess.call('mv *.fits raw', shell=True)

