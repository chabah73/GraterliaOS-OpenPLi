# the implementation here is a bit crappy.
import time
from Directories import resolveFilename, SCOPE_CONFIG, fileExists
from GOSHardwareInfo import GOSHardwareInfo

vfdSIZE = GOSHardwareInfo().get_vfdsize()
if GOSHardwareInfo().get_rcstype() == 'UHD88':
    vfdSIZE += 1


PERCENTAGE_START = 20
PERCENTAGE_END = 100
LAST_PERCENTAGE = 0
profile_start = time.time()

profile_data = {}
total_time = 1
profile_file = None
LastVFDtext = ""

try:
	profile_old = open(resolveFilename(SCOPE_CONFIG, "profile"), "r").readlines()

	t = None
	for line in profile_old:
		(t, id) = line[:-1].split('\t')
		t = float(t)
		total_time = t
		profile_data[id] = t
	if total_time == 0:
		total_time = 1
except:
	print "no profile data available"

try:
	profile_file = open(resolveFilename(SCOPE_CONFIG, "profile"), "w")
	
	
except IOError:
	print "WARNING: couldn't open profile file!"

def profile(id):
	global LastVFDtext, LAST_PERCENTAGE
	now = time.time() - profile_start
	if profile_file:
		profile_file.write("%.2f\t%s\n" % (now, id))
		print ("%s\t%.2f\t%s\n" % (time.strftime("%H:%M:%S", time.localtime()), now, id))

		if id in profile_data:
			t = profile_data[id]
			perc = t * (PERCENTAGE_END - PERCENTAGE_START) / total_time + PERCENTAGE_START
			if perc > LAST_PERCENTAGE:
				if vfdSIZE == 4:
					CurrentText = "E2-%d" % (perc - 1)
					CurrentText = CurrentText[0:4]
				if vfdSIZE == 5:
					CurrentText = "E2:%d" % (perc - 1)
					CurrentText = CurrentText[0:5]
				elif vfdSIZE == 8:
					CurrentText = "GOS-%d" % (perc)
					CurrentText = CurrentText[0:8]
				else:  
					CurrentText = "Start GOS-%d" % (perc)
					CurrentText = CurrentText[0:14]
				try:
					open("/proc/progress", "w").write("%d \n" % perc)
					if LastVFDtext != CurrentText and perc < 100:
						print "[Profile] %s" % CurrentText
						open("/dev/vfd", "w").write(CurrentText)
						LastVFDtext = CurrentText
				except IOError:
					pass
				LAST_PERCENTAGE = perc #na koncu, aby przy ewentualnym bledzie vfd nie blokowac ponownego wpisu

def profile_final():
	try:
		open("/proc/progress", "w").write("100 \n")
	except:
		pass
	global profile_file
	if profile_file is not None:
		profile_file.close()
		profile_file = None
	