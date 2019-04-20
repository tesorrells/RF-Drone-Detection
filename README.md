# Passive RF Drone Detection for the Georgia Tech Police Department
Team members:
- Anya Bhatnagar
- Kenneth Hyman
- Frederic Faulkner
- James Smith
- Trevor Sorrells

## Summary
This aim of this project is to research and evaluate different methods for passively detecting the presence of drones by analyzing drone and controller Radio Frequency communications. As such, documentation will be divided according by methodology as follows:

1. [Hardware Setup](#1-hardware-setup)
   - 1.1. Nvidia Jetson Tegra TK1 - *only necessary if deploying a sensor in the future*
2. [Software Setup](#2-software-setup)
   - 2.1. HackRF One Tools
   - 2.2. GNU Radio
2. [Detection Methodologies](#3-detection-methodologies)
   - 3.1. HackRF Sweep
   - 3.2. GNU Radio
   - 3.3. Wi-Fi Detection

# 1. Hardware Setup
## 1.1 Nvidia Jetson Tegra TK1
If any of the detection methodologies are to be deployed in the future, they will need to be hosted on a Linux computer. GTRI provided us with several [Nvidia Jetson TK1](https://www.nvidia.com/object/jetson-tk1-embedded-dev-kit.html) development boards for prototyping.

This section describes how to get the Jetson Tegra TK1 up and running.

### Important Notes: Read Before Proceeding
1. **NEVER** attempt to upgrade the distribution on the TK1, i.e. running `sudo apt-get dist-upgrade`. This will overwrite important Jetson Tegra TK1 files and render the system inoperable. You will then have to reflash the system as described below. Always follow NVIDIA's directions for upgrading the system: We have had no issues running normal updates via `sudo apt-get update`.

2. Use `tmux` or `screen` when running important commands over ssh, in case the connection is lost.

3. Secure Shell: By default, you can only connect to the TK1 using ssh password authentication from the local network. In order to connect remotely, you will have to use public key authentication.

4. Make sure to have a USB-RS232 serial adapter available with Null Modem adapter. This provides a more reliable method of communication with the device than SSH / HDMI when something goes awry. *Also note that the serial console is unsecured by default.*

5. Although the Jetson has a built-in HDMI video output, we had issues using it. It is best to connect to the Jetson over a serial or SSH connection.

### Initial Hardware Setup

Use a program such as *screen* or *minicom* from your Ubuntu desktop to connect over serial using a USB-RS232 serial adapter with Null Modem Adapter.
```sh
# Example using screen
sudo screen /dev/ttyUSB0 115200
```

### Flashing the Jetson Tegra TK1
#### Important Notes BEFORE Flashing
While you *may* be able to flash using the Jetson Jetpack GUI, we found it more straightforward to reflash from the command line using Ubuntu. We found that using the official Jetson Jetpack GUI to flash does not work with Ubuntu 18.04+ -- it requires Ubuntu 16.04 and a newer Jetson model.

It is unclear if flashing using this method through a virtual machine is possible.

We *highly* recommend flashing from a Ubuntu 18.04 machine through the command line, as this is the method we had success with.

#### Flashing Instructions
Flashing the TK1 may be necessary initially or if the system becomes corrupted. As of the writing of this document, R21.7 is the most recent release. The main page for the release [can be found here](https://developer.nvidia.com/linux-tegra-r217).

Directions for flashing the device can be found in that page following the [R21.7 Quick Start Guide](https://developer.nvidia.com/embedded/dlc/quick-start-guide-r217) link, but make sure to observe the notes above and the note below (in the likely event your Ubuntu computer is 64-bit).

> #### Flashing from 64-bit Ubuntu 18.04
>If on a 64-bit host, there is an issue you will need to address.
>```sh
># Replace this line of Linux_for_Tegra/flash.sh:
>mkfs -t $4 ${loop_dev} > /dev/null 2>&1;
># With this line
>mkfs -t $4 -O ^metadata_csum,^64bit ${loop_dev} > /dev/null 2>&1;
>```
>The original post describing this issue and fix can [be found here](https://devtalk.nvidia.com/default/topic/1037298/jetson-tk1/flash-tk1-from-ubuntu-18-04-/) on Nvidia's forum.


#### After Sucessful Flash
##### Update Jetson's Ubuntu Repositories
Again, make sure to have serial console access for troubleshooting.

Run the following commands on your Jetson to set the password for the `ubuntu` user, activate the Ubuntu Universe repository, and install a few useful tools:
```sh
# Change default password for user ubuntu
# Make sure to make note of the new password.
sudo passwd ubuntu
# Enable the Universe repo and update
sudo add-apt-repository universe
sudo apt-get update
sudo apt-get upgrade
# You may want to install some useful programs at this point
sudo apt-get install -y tmux htop screen git bash-completion nano
```
You may want to change the name of the Jetson device. To do so, change 'tegra-ubuntu' to the desired new name in `/etc/hostname` and `/etc/hosts`.

For example:
1. type the command `sudo nano /etc/hostname` and hit `ENTER`.
2. Change 'tegra-ubuntu' to your desire hostname.
3. Hit `CTRL-X` and the `Y` to save.

Repeat steps 1-3 for `/etc/hosts` as well.

(This will not change until reboot, so you can either reboot (`sudo reboot`) or run `sudo hostname YOUR-NEW-HOSTNAME-HERE` to avoid rebooting.)

##### Additional Steps to Consider
Although not necessary for our prototyping purposes, the following should be considered if deploying the Jetson in a production environment.
- Create/modify a  master `/etc/ssh/sshd_config` config file for the Jetson SSH server.
- Create & copy SSH public keys to the Jetson using `ssh-copy-id -i your-key-here jetson-hostname-here` or manually.
- Configure a firewall, such as `ufw`, as there is none active by default.

# 2. Software Setup

## 2.1 HackRF One Tools Installation
`hackrf_sweep` is a tool provided by the creators of the HackRF One that scans a given frequency range and outputs the measurements as a comma separated value (csv) file.

### Build & Installation Instructions
In order to use hackrf_sweep, we need to install the HackRF tools. These directions are the same whether you are installing them on the Jetson or your Ubuntu computer.

Follow directions on https://github.com/mossmann/hackrf/tree/master/host
(This doesn't take very long to build, maybe a few minutes.)

You will also need to make sure that your user (ubuntu) is a member of the *plugdev* group. Simply enter ```sudo usermod -a -G plugdev ubuntu```. Then reboot the Jetson and type `groups` to verify that ubuntu is a member of *plugdev*.

There is an issue with the HackRF on many distribution sin which computer will auto-suspend the USB by default, causing instability and the inability to get measurements from the HackRF. We want to disable this and reboot the tegra. Add the following line to `/etc/rc.local` and then reboot ([source](https://elinux.org/Jetson/Performance#Maximizing_CPU_performance)):
```
echo -1 > /sys/module/usbcore/parameters/autosuspend
```

Finally, run the `hackrf_info` command.

If everything installed correctly, you should see something like the following:

```
hackrf_info version: 2017.02.1
libhackrf version: 2017.02.1 (0.5)
Found HackRF
Index: 0
Serial number: 0000000000000000################
Board ID Number: 2 (HackRF One)
Firmware Version: 2017.02.1 (API:1.02)
Part ID Number: 0x######## 0x########
```

## 2.2 GNU Radio Installation
[GNU Radio](https://www.gnuradio.org/) is an advanced tool used in our detection methodology as described in [section 3.2](#32-gnu-radio).

From gnuradio.org:
>GNU Radio is a free & open-source software development toolkit that provides signal processing blocks to implement software radios. It can be used with readily-available low-cost external RF hardware to create software-defined radios, or without hardware in a simulation-like environment. It is widely used in research, industry, academia, government, and hobbyist environments to support both wireless communications research and real-world radio systems.

### Installation Instructions
We used GNU Radio on an Ubuntu 18.04 64-bit laptop to observe communications between a DJI Phantom II and its controller and to attempt to measure drone body vibrations using two HackRF One devices (see 3.2). It is also possible to install GNU Radio on the Jetson, although this proved to be unnecessary for our research.

Unless there is a compelling reason, you want to use the version of GNU Radio that comes in the Ubuntu 18.04 repositories.
```sh
sudo apt-get install gnuradio
```
> Details for other distributions/OS's can be found on the [GNU Radio Wiki](https://wiki.gnuradio.org/index.php/InstallingGR)

It is also possible to [build and install GNU Radio from source](https://wiki.gnuradio.org/index.php/InstallingGRFromSource#Using-the-build-gnuradio-script), although the process is far more complicated and time intensive.

# 3. Detection Methodologies
## 3.1. HackRF Sweep
## 3.2. GNU Radio
## 3.3. Wi-Fi Detection
### Description
```bash
$ sudo python3 ./wifi_monitor.py wlan0
```
wifi_monitor.py will put the wireless card into monitor mode and begin listening for broadcasts that match one of the masks in `oui_list`. Currently, it listens for MAC addresses that start with `62:60:1F` or `60:60:1F` (which belong to DJI).

### Requirements
- Python3
- Root permissions
- Airodump-ng (part of Aircrack-ng)
	- Tested with version 1.2 rc4 on Ubuntu 18.04
	- https://aircrack-ng.org/
- Wifi Adapter capable of [**monitor mode**]([https://aircrack-ng.org/doku.php?id=compatible_cards)
	- Tested with TP-Link TLWN722N (FCC ID: TE7WNN722N), which is 2.4Ghz only.

### Usage
Airodump-ng and Airmon-ng require that wifi_monitor.py be run with root permissions.

#### Interface selection
If there is only one wifi interface, wifi_monitor will automatically select and use it, so there is no need to pass it as an interface as an argument when run. This  will suffice:
```bash
$ sudo python3 ./wifi_monitor.py
```
Otherwise, you can find the wifi interfaces with `iw dev`, which will produce output something like:

```bash
$ iw dev
phy#0
	Interface wlan0
		ifindex 219
		wdev 0x500000001
		addr a0:f3:xx:xx:xx:xx
		txpower 20.00 dBm
phy#1
	Interface wlan1
		ifindex 180
		wdev 0x1c
		addr b8:08:xx:xx:xx:xx
		type managed
```

You will want use the `Interface wlan0` portion, not the `phy#0`. Note that in some distributions, the interface may be names differently (such as `wlxa0f3c11e13c2`, for example).

If the wireless interface to be used is **wlan0**, you would enter the following:
```sudo python3 ./wifi_monitor.py wlan0```

### To Do
- add MAC address masks for other drone manufacturers
- include 5Ghz wifi communication
- move MAC address masks from a `oui_list` to an external file (?)
