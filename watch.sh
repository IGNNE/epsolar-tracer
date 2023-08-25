#!/bin/bash

# small script to log info.py to a file, could probably be done in python as well, but hey, works

while true; do
date >> log.txt
python3 info.py | grep -vE "Carbon|rated|Light|Day|timing|time" | uniq >> log.txt
echo "" >> log.txt
sleep 10
done
