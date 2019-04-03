#! /usr/bin/env python3
import io
import logging
import os
import subprocess
import sys
import time


class Airodumper:
    # ref: https://github.com/atiti/airodump-logger/blob/master/airodump.py
    ap_list = {}
    client_list = {}
    proc = None
    interfaces = []
    monitor_interfaces = []
    iface = None

    def __init__(self):
        if not os.geteuid() == 0:
            logging.error("Must run as root")
            sys.exit('This script must be run as root!')
        self.choose_interface()

    def get_interfaces(self):
        logging.debug("Getting interfaces...")
        try:
            with subprocess.Popen(['airmon-ng'], bufsize=1, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT) as mon_proc:
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
            with subprocess.Popen(['airmon-ng', 'stop', iface], stdout=subprocess.PIPE) as stop_proc:
                stop_proc.wait()
        self.get_interfaces()
        logging.info("Monitor mode stopped for all interfaces...")

    def choose_interface(self):
        self.stop_monitor_mode()
        if len(self.interfaces) > 1:  # multiple interfaces found
            if len(sys.argv) > 1:  # interface specified as cmd line arg
                if sys.argv[1] not in self.interfaces:  # erroneous interface specified
                    sys.exit("Specified interface not found!\nUsage: sudo ./wifi_monitor.py wlan0")
                else:  # specified interface IS in self.interfaces
                    self.iface = sys.argv[1]
            else:
                sys.exit("Error: Must specify an interface when multiple are found. Run 'iw dev' for options.")
        else:  # Only one interface found
            self.iface = self.interfaces[0]
        logging.info("Selected " + self.iface)

        if self.iface not in self.monitor_interfaces:
            with subprocess.Popen(['airmon-ng', 'start', self.iface], stdout=subprocess.PIPE) as start_proc:
                start_proc.wait()
                self.get_interfaces()
                if len(self.monitor_interfaces) != 1:
                    sys.exit("Error. Should be exactly one monitor interface")
                self.iface = self.monitor_interfaces[0]
        logging.info("Finally chose " + repr(self.iface))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        print("Specified interface: " + sys.argv[1])
    dumper = Airodumper()
