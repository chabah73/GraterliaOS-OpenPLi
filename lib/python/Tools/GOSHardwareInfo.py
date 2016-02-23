import os

rcstype = None
vfdsize = 4
boxtype = None 
if os.path.exists("/var/grun/grcstype"):
    with open ("/var/grun/grcstype", "r") as myconfigfile:
        for line in myconfigfile:
            line = line.strip()
            if line.startswith('rcstype='):
                rcstype = line.split("=")[1]
            elif line.startswith('vfdsize='):
                vfdsize = int(line.split("=")[1])
            elif line.startswith('boxtype='):
                boxtype =  line.split("=")[1]
else:
    rcstype = open("/proc/stb/info/model").read().strip()
    boxtype = rcstype
print "Detected: rcstype=%s, vfdsize=%d, boxtype=%s" % (rcstype,vfdsize,boxtype)

class GOSHardwareInfo:
    def get_rcstype(self):
        return rcstype

    def get_vfdsize(self):
        return vfdsize

    def get_boxtype(self):
        return boxtype
