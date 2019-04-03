#! /usr/bin/env python3
import io
import logging
import os
import subprocess
import sys


class Airodumper:
    # ref: https://github.com/atiti/airodump-logger/blob/master/airodump.py
    ap_list = {}
    client_list = {}
    proc = None
    interfaces = []
    monitor_interfaces = []

    def __init__(self):
        if not os.geteuid() == 0:
            logging.error("Must run as root")
            sys.exit('This script must be run as root!')
        self.choose_interface()

    def get_interfaces(self):
        logging.debug("Getting interfaces...")
        try:
            with subprocess.Popen(['airmon-ng'], bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as mon_proc:
                mon_proc.wait()
                # Get wifi interfaces
                self.interfaces = []
                self.monitor_interfaces = []
                for line in io.TextIOWrapper(mon_proc.stdout):
                    tmp = line.rstrip().split("\t")
                    if "phy" in tmp[0]:
                        logging.debug("Found interface " + tmp[1] + " on " + tmp[0])
                        self.interfaces.append(tmp[1])
                        if "mon" in tmp[1]:  # is interface in monitor mode already?
                            logging.debug("\tinterface " + tmp[1] + " already in monitor mode")
                            self.monitor_interfaces.append(tmp[1])
                logging.info("Found interfaces: " + repr(self.interfaces))
                if len(self.interfaces) < 1:
                    raise ValueError
        except FileNotFoundError:
            logging.error("aircrack-ng suite not found in PATH")
            sys.exit("Error: either aircrack-ng suite is not installed or not in PATH. Install from "
                     "https://github.com/aircrack-ng/aircrack-ng ... Aborting")
        except ValueError:
            logging.error("Didn't find any wifi interfaces with airmon-ng")
            sys.exit("Didn't find any wifi interfaces with airmon-ng... Aborting")

    def stop_monitor_mode(self):
        logging.info("Stopping monitor mode for all interfaces...")
        self.get_interfaces()
        for iface in self.monitor_interfaces:
            logging.info("Stopping monitor mode for " + iface)
            stop_proc = subprocess.Popen(['airmon-ng', 'stop', iface], bufsize=1, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT)
            stop_proc.wait()
        self.get_interfaces()
        logging.info("Monitor mode stopped for all interfaces...")

    def choose_interface(self):
        self.stop_monitor_mode()
        print("Select interface:")
        for i, iface in enumerate(self.interfaces):
            print("%s\t%s" % (i, iface))
        choice = None
        while choice not in range(0, len(self.interfaces)):
            try:
                choice = int(input("Enter your selection & hit [Enter]: "))
            except ValueError:
                pass
        logging.info("chose: " + self.interfaces[choice])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dumper = Airodumper()
