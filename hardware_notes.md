# Important Notes
- IMPORTANT: NEVER run 'sudo apt-get dist-upgrade'. This will overwrite important Jetson Tegra TK1 files and render the system inoperable. Follow NVIDIA's directions for upgrading the system.
- Try to use tmux or screen when running imporant commands over ssh, in case the connection is lost.
- SSH: By default, you can only connect to the TK1 using ssh password authentication from the local network. In order to connect remotely, you will have to use public key authentication.

# Initial Hardware Setup
## Flashing the Jetson Tegra TK1
- [Go to 'Tegra K1' Section](https://developer.nvidia.com/embedded/linux-tegra-archive) and select most recent release. As of the writing of this document, R21.7 is the most recent. Directions for reflashing the device can be found in the *Quick Start Guide*.

# Installing GNU Radio
To install gnuradio, use gnuradios build system called PyBOMBS (link below). The Ubuntu Universe repository version tends to be outdated. Build gnuradio using PyBOMBS from source following [these directions](https://github.com/gnuradio/pybombs/). This takes a significant amount of time. I had trouble using `sudo pip install PyBOMBS`, so instead use `$ [sudo] pip install git+https://github.com/gnuradio/pybombs.git` to install the latest version from git.
