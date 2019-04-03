#! /usr/bin/env python3
import os, subprocess, sys
import time
import io, logging


class Airodumper:
    # ref: https://github.com/atiti/airodump-logger/blob/master/airodump.py
    ap_list = {}
    client_list = {}
    proc = None
    interfaces = []

    def __init__(self):
        self.get_interfaces()

    def get_interfaces(self):
        if not os.geteuid() == 0:
            sys.exit('This script must be run as root!')
        try:
            self.proc = subprocess.Popen(['airmon-ng'], bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.proc.wait()

            self.interfaces = []
            for line in io.TextIOWrapper(self.proc.stdout):
                tmp = line.rstrip().split("\t")
                if "phy" in tmp[0]:
                    logging.info("Interface: " + repr(tmp))
                    self.interfaces.append(tmp[1])
            logging.info("Found interfaces: " + repr(self.interfaces))
        except FileNotFoundError:
            logging.error("aircrack-ng suite not found in PATH")
            sys.exit("Error: either aircrack-ng suite is not installed or not in PATH. Install from "
                     "https://github.com/aircrack-ng/aircrack-ng")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dumper = Airodumper()
