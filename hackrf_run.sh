#!/bin/bash
SAMPLE_DURATION=30
read -p "Enter filename: " FILENAME
FILENAME="$FILENAME.csv"
echo $FILENAME
if [ ! -f $FILENAME ]; then
	echo "Starting to log data"
	timeout $SAMPLE_DURATION hackrf_sweep -f 2400:2500 -n 8192 -w 600000 -r $FILENAME
else
	echo "File Already exists!!"
fi
