#! /usr/bin/env python3
import os, subprocess, sys
import time
import io


class Airodumper:
    # ref: https://github.com/atiti/airodump-logger/blob/master/airodump.py
    ap_list = {}
    client_list = {}
    proc = None

    def __init__(self):
        self.get_interfaces()

    def get_interfaces(self):
        if not os.geteuid() == 0:
            sys.exit('This script must be run as root!')
        try:
            self.proc = subprocess.Popen(['airmon-ng'], bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.proc.wait()
            for line in io.TextIOWrapper(self.proc.stdout):
                tmp = line.rstrip().split("\t")
                if "phy" in tmp[0]:
                    print("temp: ", tmp)
        except FileNotFoundError:
            sys.exit("Error: either aircrack-ng suite is not installed or not in PATH. Install from "
                     "https://github.com/aircrack-ng/aircrack-ng")


if __name__ == '__main__':
    dumper = Airodumper()
