import os
from .base.build import *


cwd = os.getcwd()
path = os.path.join(cwd, 'otp', 'rtp')


def rtp_build():
    clean(path)
    copy(path)
    build(path)


def main():
    pass

