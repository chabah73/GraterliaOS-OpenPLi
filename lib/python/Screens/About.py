import sys
import os
import time
from Tools.Directories import resolveFilename, SCOPE_SYSETC
from os import popen

def getVersionString():
	return getImageVersionString()

#def getImageVersionString():
#	try:
#		if os.path.isfile('/var/lib/opkg/status'):
#			st = os.stat('/var/lib/opkg/status')
#		else:
#			st = os.stat('/usr/lib/ipkg/status')
#		tm = time.localtime(st.st_mtime)
#		if tm.tm_year >= 2011:
#			return time.strftime("%Y-%m-%d %H:%M:%S", tm)
#	except:
#		pass
#	return _("unavailable")

def getImageVersionString():
		try:
			file = open(resolveFilename(SCOPE_SYSETC, 'image-version'), 'r')
			lines = file.readlines()
			for x in lines:
				splitted = x.split('=')
				if splitted[0] == "version":
					#     YYYY MM DD hh mm
					#0120 2005 11 29 01 16
					#0123 4567 89 01 23 45
					version = splitted[1]
					image_type = version[0] # 0 = release, 1 = experimental
					major = version[1]
					minor = version[2]
					revision = version[3]
					year = version[4:8]
					month = version[8:10]
					day = version[10:12]
					date = '-'.join((year, month, day))
					if image_type == '0':
						image_type = "Release"
						version = '.'.join((major, minor, revision))
						return ' '.join((image_type, version, date))
					else:
						image_type = "Experimental"
						return ' '.join((image_type, date))
			file.close()
		except IOError:
			pass

		return _("unavailable")


def getEnigmaVersionString():
	import enigma
	enigma_version = enigma.getEnigmaVersionString()
	if '-(no branch)' in enigma_version:
		enigma_version = enigma_version [:-12]
	return enigma_version

def getKernelVersionString():
	try:
		return open("/proc/version","r").read().split(' ', 4)[2].split('-',2)[0]
	except:
		return _("unknown")

def getHardwareTypeString():
	try:
		if os.path.isfile("/proc/stb/info/boxtype"):
			return open("/proc/stb/info/boxtype").read().strip().upper() + " (" + open("/proc/stb/info/board_revision").read().strip() + "-" + open("/proc/stb/info/version").read().strip() + ")"
		if os.path.isfile("/proc/stb/info/vumodel"):
			return "VU+" + open("/proc/stb/info/vumodel").read().strip().upper() + "(" + open("/proc/stb/info/version").read().strip().upper() + ")" 
		if os.path.isfile("/proc/stb/info/model"):
			return open("/proc/stb/info/model").read().strip().upper()
	except:
		pass
	return _("unavailable")

def getImageTypeString():
	try:
		return open("/etc/issue").readlines()[-2].capitalize().strip()[:-6]
	except:
		pass
	return _("undefined")

# For modules that do "from About import about"
about = sys.modules[__name__]
