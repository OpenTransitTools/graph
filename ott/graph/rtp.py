import os
from ott.utils import file_utils

path = os.path.join('otp', 'rtp')
gtfs = os.path.join('..', 'gtfs')

def build():
    n = file_utils.find_files_in_subdirs(path, ext=".zip")
    print(n)
    file_utils.purge(path, ".*.zip")
    n = file_utils.find_files_in_subdirs(path, ext=".zip")
    print(n)
    file_utils.copy_contents(gtfs, path)
    n = file_utils.find_files_in_subdirs(path, ext=".zip")
    print(n)
    #file_utils.cd(path)
    #print(path, x)


def main():
    pass