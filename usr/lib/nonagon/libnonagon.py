#!/usr/bin/python
#####################################
# Made by a kitty on a pts
#####################################
# General TC documentaion : http://wiki.linuxwall.info/doku.php/en:ressources:dossiers:networking:traffic_control
################
import os, subprocess, json, shlex

def intsettings(settings):
	myifls = []
	rawifs = open(settings['interfaces'], "r")
	iflsn = rawifs.readlines()
	rawifs.close()
	for ifacen in iflsn:
		templs = ifacen.rstrip()
		myifls.extend(templs.split())
	settings['ifls'] = myifls
	classbase = (int(settings['ceil']) / int(settings['classdivide']))
	classrange = (float(classbase) * float(settings['ceilrange']))
	settings['classbase'] = int(classbase)
	settings['burstclass'] = int(settings['classbase'] + classrange)
	return(settings)

def setbwclass(settings):
	cmdlist = []
	myclass = settings['burstclass']
	myclassbase = settings['classbase']
	while int(settings['ceil']) >= myclass:
		for iface in settings['ifls']:
			cmdlist.extend([settings['tc'] + " class add dev " + iface + " parent 1:" + str(myclassbase)  + " classid 1:" + str(myclassbase) + " htb rate " + str(myclassbase) + "mbit ceil " + str(myclass) + "mbit burst 15k"])
			cmdlist.extend([settings['tc'] + " qdisc add dev " + iface + " parent 1:" + str(myclassbase) + " handle " + str(myclassbase) + " sfq perturb " + settings['perturb'] + " limit " + settings['sfqlimit']])
		myclassbase = int(myclassbase + settings['classbase'])
		myclass = int(myclass + settings['classbase'])
	for iface in settings['ifls']:
		cmdlist.extend([settings['tc'] + " class add dev " + iface + " parent 1:" + str(settings['ceil']) + " classid 1:" + str(settings['ceil']) + " htb rate " + str(settings['ceil']) + "mbit ceil " + str(settings['ceil']) + "mbit burst 15k"])
		cmdlist.extend([settings['tc'] + " qdisc add dev " + iface + " parent 1:" + str(settings['ceil']) + " handle " + str(settings['ceil']) + " sfq perturb " + settings['perturb'] + " limit " + settings['sfqlimit']])
	for cmd in cmdlist:
		print cmd
		subprocess.check_call(shlex.split(cmd))

def sethosts(settings):
	jsonconfls = []
	for rootpath, dirnames, filenames in os.walk(settings['flowlist']):
		for filename in filenames:
			mypath = settings['flowlist'] + "/" + filename
			jsonconfls.append(json.loads(open(mypath).read()))
	cmdlist = []
	ipcmdls = []
	ipcmdls.extend([settings['ipt'] + " -t mangle -A POSTROUTING -j CONNMARK --restore-mark"])
	for jflows in jsonconfls:
		cmdlist.extend([settings['tc'] + " filter add dev " + jflows['external'] + " parent 1:0 protocol ip prio " + jflows['priority'] + " handle " + jflows['downspeed'] + " fw flowid 1:" + jflows['downspeed']])
		cmdlist.extend([settings['tc'] + " filter add dev " + jflows['internal'] + " parent 1:0 protocol ip prio " + jflows['priority'] + " handle " + jflows['upspeed'] + " fw flowid 1:" + jflows['upspeed']])
		ipcmdls.extend([settings['ipt'] + " -t mangle -A POSTROUTING -o " + jflows['external'] + " -s " + jflows['outaddr'] + " -j CONNMARK --set-mark " + jflows['downspeed']])
		ipcmdls.extend([settings['ipt'] + " -t mangle -A POSTROUTING -o " + jflows['internal'] + " -d " + jflows['inaddr'] + " -j CONNMARK --set-mark " + jflows['upspeed']])
	for cmd in cmdlist:
		print cmd
		subprocess.check_call(shlex.split(cmd))
	for ipcmd in ipcmdls:
		print ipcmd
		subprocess.check_call(shlex.split(ipcmd))

def start(settings):
	cmdlist = []
	for iface in settings['ifls']:
		cmdlist.extend([settings['tc'] + " qdisc add dev " + iface + " root handle 1: htb default " + settings['ceil']])
		cmdlist.extend([settings['tc'] + " class add dev " + iface + " parent 1: classid 1:1 htb rate " + settings['ceil'] + "mbit burst 15k"])
	for cmd in cmdlist:
		print cmd
		subprocess.check_call(shlex.split(cmd))
	setbwclass(settings)
	sethosts(settings)

def stop(settings):
	cmdlist = []
	ipcmdls = []
	jsonconfls = []
	for rootpath, dirnames, filenames in os.walk(settings['flowlist']):
		for filename in filenames:
			mypath = settings['flowlist'] + "/" + filename
			jsonconfls.append(json.loads(open(mypath).read()))
	for iface in settings['ifls']:
		cmdlist.extend([settings['tc'] + " qdisc del dev " + iface + " root"])
	for jflows in jsonconfls:
		ipcmdls.extend([settings['ipt'] + " -t mangle -A POSTROUTING -o " + jflows['external'] + " -s " + jflows['outaddr'] + " -j CONNMARK --set-mark " + jflows['downspeed']])
		ipcmdls.extend([settings['ipt'] + " -t mangle -A POSTROUTING -o " + jflows['internal'] + " -d " + jflows['inaddr'] + " -j CONNMARK --set-mark " + jflows['upspeed']])
	for cmd in (cmdlist):
		print cmd
		subprocess.check_call(shlex.split(cmd))
	for ipcmd in (ipcmdls):
		print ipcmd
		subprocess.check_call(shlex.split(ipcmd))

def status(settings):
	cmdlist = []
	for iface in settings['ifls']:
		cmdlist.extend([settings['tc'] + " -s -d qdisc show dev " + iface])
		cmdlist.extend([settings['tc'] + " -s -d class show dev " + iface])
		cmdlist.extend([settings['tc'] + " -s -d filter show dev " + iface + " parent 1:1"])
	for cmd in (cmdlist):
		myoutput = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(myout, myerr) = myoutput.communicate()
		mystatus = myoutput.wait()
		print cmd
		print myout
		print "return code:", mystatus
