import matplotlib.pyplot as plt
from dateutil.parser import parse

# analyze the logs created by watch.sh

f = open("log.txt", "r")

times = []
input_ws = []
output_ws = []
socs = []

for l in f:
    if "BST" in l:
        times.append(parse(l))
    if "Charging equipment input power = " in l:
        input_ws.append(float((l.split(" ")[-1])[0:-2]))
    if "Battery SOC" in l:
        socs.append(float((l.split(" ")[-1])[0:-2]))
    if "Discharging equipment output power = " in l:
        output_ws.append(float((l.split(" ")[-1])[0:-2]))


fig, axs = plt.subplots(3, 1, sharex=True)
axs[0].step(times, input_ws)
axs[0].set_title("Input W")
axs[0].grid(True)
axs[1].step(times, output_ws)
axs[1].set_title("Output W")
axs[1].grid(True)
axs[2].step(times, socs)
axs[2].set_title("State of Charge")
axs[2].grid(True)


plt.show()
