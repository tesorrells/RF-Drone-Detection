# Passive RF Drone Detection for the Georgia Tech Police Department
Team members:
- Anya Bhatnagar
- Kenneth Hyman
- Frederic Faulkner
- James Smith
- Trevor Sorrells

## Version 1.0.0
This is the initial release of our drone detection device. Previous releases leading up to this have consisted of research, experiments and data visualization tools.

### New Features
- With this version we are releasing a script that is capable of monitoring local Wi-Fi activity. Continue reading for usage instruction for `wifi_monitor.py`.
- This release also came with a large amount of documentation and a clean up of our git branching

### Known Issues and Proposed Fixes
Our method of detection relies on looking at mac addresses in the local area and checking if their OUI matches that of any drone manufacturers. As such, we are vulnerable to any mac address spoofing and risk the chance of having false positives for non-drone devices by these same manufacturers.

One possible solution that could address both of the above problems would be to use a model that can detect noise in the signal that is indicative of drone body vibration. This mechanism as well as experiments that can be used to move forward with this solution are outlined later in this document.


## Summary
This aim of this project is to research and evaluate different methods for passively detecting the presence of drones by analyzing drone and controller Radio Frequency communications. As such, the documentation is divided into Setup (Hardware & Software) and Detection Methodologies.

1. [Hardware Setup](#1-hardware-setup)
   - 1.1. Nvidia Jetson Tegra TK1 - *only necessary if deploying a sensor in the future*
2. [Software Setup](#2-software-setup)
   - 2.1. HackRF One Tools
   - 2.2. GNU Radio
3. [Detection Methodologies](#3-detection-methodologies-and-research)
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


#### After Successful Flash
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

# 3. Detection Methodologies and Research
## 3.1. HackRF Sweep Experiment
We attempted to make use of the data gathered using the [HackRF sweep functionality](https://github.com/mossmann/hackrf/wiki/hackrf_sweep) on the 2.4GHz range to determine if any given activity was coming from a drone. This research experiment was designed to create data similar to that used in the [research performed at Colorado](http://www.cs.colorado.edu/~rhan/Papers/p17-nguyen.pdf).

With the experiment's data, we attempted to use a FFT see if there is any high frequency, low amplitude noise coming from the drone signal that could indicate body vibration caused by the propellers in motion. While we were not able to successfully recreate these visualizations or model this behavior in a way suitable for detection, we believe the data we collected could be further experimented with to do so.

Refer to [Experiment 3](Experiment_Outline.md#experiment-plan-3)

### Description of tools
#### Collecting hackrf_sweep Data
[hackrf_sweep-collect-data.sh](src/hackrf_sweep-collect-data.sh)

Runs `hackrf_sweep`  for 60 seconds and prompts the user for a filename to save the CSV data to. It uses the following parameters:

| parameter | value |
|--|--|
| freq_min | 2400 (MHz) |
| freq_max    | 2500 (MHz)   |
|num_samples   | 8192   |
|bin_width   | 600000   |

Details can be found in hackrf_sweep's documentation:
```bash
$ hackrf_sweep -h    
Usage:
	[-h] # this help
	[-d serial_number] # Serial number of desired HackRF
	[-a amp_enable] # RX RF amplifier 1=Enable, 0=Disable
	[-f freq_min:freq_max] # minimum and maximum frequencies in MHz
	[-p antenna_enable] # Antenna port power, 1=Enable, 0=Disable
	[-l gain_db] # RX LNA (IF) gain, 0-40dB, 8dB steps
	[-g gain_db] # RX VGA (baseband) gain, 0-62dB, 2dB steps
	[-n num_samples] # Number of samples per frequency, 8192-4294967296
	[-w bin_width] # FFT bin width (frequency resolution) in Hz
	[-1] # one shot mode
	[-B] # binary output
	[-I] # binary inverse FFT output
	-r filename # output file

Output fields:
	date, time, hz_low, hz_high, hz_bin_width, num_samples, dB, dB, . . .

```

#### Processing hackrf_sweep data
[hackrf_sweep-process-data.py](src/hackrf_sweep-process-data.py)

This Python script is used to process and visualize the data output from hackrf_sweep.

##### Requirements:
- Python3
- pipenv
- pip3

##### Installation
To install the requirements for Ubuntu 18.04:
```bash
sudo apt install python3 pip3
pip3 install --user pipenv
git clone git@github.com:tesorrells/RF-Drone-Detection.git
cd ./RF-Drone-Detection
```

##### Usage
To process the output data from the hackrf_sweep:
```bash
cd ./RF-Drone-Detection
pipenv shell # activate shell from Pipfile
python3 ./src/hackrf_sweep-process-data.py
```
Further details and documentation can be found in: [src/hackrf_sweep-process-data.py](src/hackrf_sweep-process-data.py)

## 3.2. GNU Radio Experiment
In an attempt to recreate an experiment described in [section 2.3.2 of the previously mentioned paper](http://www.cs.colorado.edu/~rhan/Papers/p17-nguyen.pdf), we made use of two simple GNU radio scripts and a HackRF attached to a drone.

The GNU Radio flow graph [gnuradio-transmit-sinewave.grc](src/gnuradio-transmit-sinewave.grc) was used to transmit a sine wave at 2.4 GHz from the HackRF attached to the drone. Its counterpart, [gnuradio-receive-sinewave.grc](src/gnuradio-receive-sinewave.grc), was used to receive the transmission.

This is another experiment used to collect data for body vibration and shifting pattern identification and would prove useful in creating a more generalize drone detection mechanism.

More details can be found in [Experiment 1](Experiment_Outline.md#experiment-plan-1) and [Experiment 2](Experiment_Outline.md#experiment-plan-2).

## 3.3. Wi-Fi Detection
### Description
Using passive Wi-Fi monitoring, we were able to identify the presence of a drone by comparing the MAC address OUI prefix (the first 24 bits of a wireless card's MAC address) to a list of known drone manufacturers.

[wifi_monitor.py](src/wifi_monitor.py) uses airodump-ng to passively listen for Wi-Fi RF communication frames.  

This was tested on a Ubuntu 18.04 laptop, but can also be used on the Jetson.

A very complete list of OUI prefixes compiled by the Wireshark team can be found [here](https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf).

### Requirements
- Python3
- Root permissions on a Ubuntu 18.04 computer
- Airodump-ng (part of the [Aircrack-ng suite](https://aircrack-ng.org/))
	- Tested with version 1.2 rc4 on Ubuntu 18.04
- Wi-Fi Adapter capable of [**monitor mode**]([https://aircrack-ng.org/doku.php?id=compatible_cards)
	- Tested with [TP-Link TLWN722N](https://www.amazon.com/s/ref=choice_dp_b?keywords=TP-Link%20TLWN722N) (FCC ID: TE7WNN722N), which is 2.4Ghz only.

### Installation
You will need to install python3 (likely already installed) and aircrack-ng on your Ubuntu 18.04 computer.

Enter the following into the terminal:
```bash
sudo apt-get install aircrack-ng python3
```
> Directions for other operating systems and distributions available at https://www.aircrack-ng.org/doku.php?id=install_aircrack

### Usage
Airodump-ng and Airmon-ng require that wifi_monitor.py be run with root permissions.

```bash
sudo python3 ./wifi_monitor.py
```
wifi_monitor.py will put the wireless card into monitor mode and begin listening for broadcasts that match one of the masks in `oui_list`. Currently, it listens for MAC addresses that start with `62:60:1F` or `60:60:1F` (which belong to DJI) and notifies the user when a drone is detected though terminal output.

#### Interface selection
If there is only one Wi-Fi interface, wifi_monitor.py will automatically select and use it, so there is no need to pass it as an interface as an argument when run. This  will suffice:
```bash
sudo python3 ./wifi_monitor.py
```
Otherwise, you can find the Wi-Fi interfaces with `iw dev`, which will produce output something like:

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

If the wireless interface to be used is **wlanx**, you would enter the following:
```bash
sudo python3 ./wifi_monitor.py wlanx
```

### Known Issues and Limitations
- Susceptible to false positives if manufacturer OUI is also used on non-drone devices
- Creating false positives is rather trivial for an attacker using the aircrack-ng tool suite
- Does not currently use 5Ghz Wi-Fi band

### Future Work
- Add MAC address masks for more drone manufacturers
- Include 5Ghz Wi-Fi communication band
- Move MAC address OUI masks to an external file
- Use SSID name to validate whether or not it is a drone/controller
