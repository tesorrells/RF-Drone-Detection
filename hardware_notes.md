# Important Notes
- IMPORTANT: NEVER run 'sudo apt-get dist-upgrade'. This will overwrite important Jetson Tegra TK1 files and render the system inoperable. Follow NVIDIA's directions for upgrading the system.
- Try to use tmux or screen when running imporant commands over ssh, in case the connection is lost.
- SSH: By default, you can only connect to the TK1 using ssh password authentication from the local network. In order to connect remotely, you will have to use public key authentication.

# Initial Hardware Setup
## Flashing the Jetson Tegra TK1
### Important Notes BEFORE Flashing
- If using the offical Jetson Jetpack to flash, it does not work with Ubuntu 18.04+. Requires Ubuntu 16.04. Unclear if flashing using this method throug a VM is possible.
- If on a 64-bit host, see [this post](https://devtalk.nvidia.com/default/topic/1037298/jetson-tk1/flash-tk1-from-ubuntu-18-04-/) for a fix.
```sh
# Replace this line of Linux_for_Tegra/flash.sh:
mkfs -t $4 ${loop_dev} > /dev/null 2>&1;
# With this line
mkfs -t $4 -O ^metadata_csum,^64bit ${loop_dev} > /dev/null 2>&1;
```

Flashing the TK1 may be necessary initially or if the system becomes corrupted. To do so, [go to 'Tegra K1' Section](https://developer.nvidia.com/embedded/linux-tegra-archive) and select most recent release. As of the writing of this document, R21.7 is the most recent. Directions for reflashing the device can be found in the *Quick Start Guide*.

# Build Instructions for HackRF Tools
Follow directions on https://github.com/mossmann/hackrf/tree/master/host

# Installing GNU Radio
To install gnuradio, use gnuradios build system called PyBOMBS (link below). The Ubuntu Universe repository version tends to be outdated. Build gnuradio using PyBOMBS from source following [these directions](https://github.com/gnuradio/pybombs/). This takes a significant amount of time. I had trouble using `sudo pip install PyBOMBS`, so instead use `$ [sudo] pip install git+https://github.com/gnuradio/pybombs.git` to install the latest version from git.
