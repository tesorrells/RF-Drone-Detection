# Wifi Monitoring
```bash
$ sudo python3 ./wifi_monitor.py wlan0
```

## Requirements
- Python3
- Root permissions
- Airodump-ng (part of Aircrack-ng)
	- Tested with version 1.2 rc4 on Ubuntu 18.04
	- https://aircrack-ng.org/
- Wifi Adapter capable of [**monitor mode**]([https://aircrack-ng.org/doku.php?id=compatible_cards)
	- Tested with TP-Link TLWN722N (FCC ID: TE7WNN722N), which is 2.4Ghz only.

## Usage
Airodump-ng and Airmon-ng require that wifi_monitor.py be run with root permissions.

### Interface selection
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
