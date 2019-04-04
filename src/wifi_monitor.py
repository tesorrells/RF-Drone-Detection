#! /usr/bin/env python3
import datetime
import io
import logging
import os
import re
import subprocess
import sys


class Airodumper:
    # ref: https://github.com/atiti/airodump-logger/blob/master/airodump.py
    ap_list = {}
    client_list = {}
    proc = None
    interfaces = []
    monitor_interfaces = []
    iface = None
    oui_list = [
        "62:60:1F",  # dji
        "60:60:1F",  # dji
        "10:",  # dummy todo remove
        "D4:",  # dummy todo remove
        "40:",  # dummy todo remove
        "38:",  # dummy todo remove
    ]  # todo consider moving to file containing drone mac OUIs

    def __init__(self):
        """
        Just check that the script is being run as root, which is needed for the aircrack-ng suite.
        """
        if not os.geteuid() == 0:
            logging.error("Must run as root")
            sys.exit('This script must be run as root!')

    def exit_on_error(self, msg: str):
        """
        Output error to log and exit with non-zero return code
        :param msg: str
        :return:
        """
        logging.error(msg)
        self.stop_monitor_mode()
        sys.exit(msg)

    def get_interfaces(self):
        """
        Get interfaces and monitor interfaces.

        """
        logging.debug("Getting interfaces with airmon-ng")
        try:
            with subprocess.Popen(['airmon-ng'], bufsize=1, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT) as mon_proc:
                mon_proc.wait(timeout=10)  # allow airmon-ng to complete.

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
                logging.info("Found monitor interfaces: " + repr(self.monitor_interfaces))
                if len(self.interfaces) == 0:
                    raise ValueError
        except FileNotFoundError:
            self.exit_on_error("Error: either aircrack-ng suite is not installed or not in PATH. Install from "
                               "https://github.com/aircrack-ng/aircrack-ng ... Aborting")
        except ValueError:
            self.exit_on_error("Didn't find any wifi interfaces with airmon-ng. Aborting.")

    def stop_monitor_mode(self):
        """
        1. refresh list of interfaces
        2. stop any monitor interfaces
        3. refresh list of interfaces
        """
        logging.info("Stopping monitor mode for all interfaces...")
        self.get_interfaces()
        for iface in self.monitor_interfaces:
            logging.info("Stopping monitor mode for " + iface)
            with subprocess.Popen(['airmon-ng', 'stop', iface], stdout=subprocess.PIPE) as stop_proc:
                stop_proc.wait()
        self.get_interfaces()
        logging.info("Monitor mode stopped for all interfaces...")

    def choose_interface(self):
        """
        Selects the wifi interface to use for passive monitoring and puts it into monitor mode.

        If there is only one wifi interface found by airmon-ng, use it.
        If there are multiple wifi interfaces found, the interface must be selected when the program is run:
        Example usage:
            sudo ./wifi_monitor.py wlan0
        (Note that you specify the original interface, not the derived monitor interface. eg wlan0mon)
        """
        self.stop_monitor_mode()
        is_argv_present = len(sys.argv) > 1
        is_multi_iface = len(self.interfaces) > 1

        # Choose interface
        if is_multi_iface:  # multiple interfaces found
            if is_argv_present:  # interface specified as cmd line arg
                argv_iface = sys.argv[1]
                if argv_iface not in self.interfaces:  # erroneous interface specified
                    sys.exit("Specified interface not found!\nUsage: sudo ./wifi_monitor.py wlan0")
                else:  # specified interface IS in self.interfaces
                    self.iface = argv_iface
            else:
                self.exit_on_error("Must specify an interface when multiple are found. Look at 'sudo airmon-ng'")
        else:  # Only one interface found. Ignore interface specified in commandline.
            self.iface = self.interfaces[0]
        logging.info("Selected " + self.iface)

        # Put interface into monitor mode if not already.
        if self.iface not in self.monitor_interfaces:
            with subprocess.Popen(['airmon-ng', 'start', self.iface], stdout=subprocess.PIPE) as start_proc:
                start_proc.wait()
                self.get_interfaces()
                if len(self.monitor_interfaces) != 1:
                    self.exit_on_error("Should be exactly one monitor interface. Aborting.")
                self.iface = self.monitor_interfaces[0]
        logging.info("Using interface " + self.iface)

    def start(self):
        """"
        Choose interface and start processing output
        """
        self.choose_interface()
        self.proc = subprocess.Popen(
            ['airodump-ng', '--update', '1', '--berlin', '20', self.iface],
            bufsize=1,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

    def stop(self):
        """
        Kill airodump-ng and turn off monitor mode.
        """
        logging.info("Stopping. Killing airodump-ng and turning off monitor mode.")
        if self.proc is not None:
            self.proc.terminate()
        self.stop_monitor_mode()

    def process(self):
        """"
        Extract observed MAC addresses from airodump-ng's output and check against MAC masks in self.oui_list
        """
        # p = re.compile(r'(?:[0-9A-F]:?){12}')  # find all mac addresses in line
        # find all mac addresses in line using regex
        p = re.compile(r'[0-9A-F]{2}\:[0-9A-F]{2}\:[0-9A-F]{2}\:[0-9A-F]{2}\:[0-9A-F]{2}\:[0-9A-F]{2}')
        for line in io.TextIOWrapper(self.proc.stdout):
            matches = re.findall(p, line.strip().upper())
            if len(matches) > 0:  # ignore empty lines
                for mac in matches:
                    logging.debug("Saw mac " + mac)
                    logging.debug(line.strip())
                    for oui in self.oui_list:
                        if str(mac).startswith(oui):
                            logging.info("Detected %s with mask %s" % (mac, oui))


if __name__ == '__main__':
    print("REMEMBER TO REMOVE DUMMY MAC ADDRESSESS!!!\n\n\n")
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        print("Specified interface: " + sys.argv[1])
    try:
        dumper = Airodumper()
        dumper.start()
        dumper.process()
    except KeyboardInterrupt:
        logging.info("got keyboard interrupt")
        dumper.stop()
