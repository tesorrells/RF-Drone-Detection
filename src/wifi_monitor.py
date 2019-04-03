#! /usr/bin/env python3
import os, subprocess, sys
from time import sleep


def check_airmon():
    try:
        proc = subprocess.Popen(['airmon-ng'])
    except FileNotFoundError:
        sys.exit("Error: either airmon-ng is not installed or not in PATH")


if __name__ == '__main__':
    # ref: https://github.com/atiti/airodump-logger/blob/master/airodump.py
    if not os.geteuid() == 0:
        sys.exit('This script must be run as root!')
    check_airmon()
    sleep(3)
