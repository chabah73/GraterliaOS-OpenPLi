installdir = $(pkglibdir)/python/Plugins/SystemPlugins

SUBDIRS = CEC PositionerSetup Satfinder \
	SkinSelector SatelliteEquipmentControl Videomode Hotplug \
	OSD3DSetup WirelessLan NetworkBrowser

if HAVE_TEMPFANCONTROL
SUBDIRS += TempFanControl
endif

if DREAMBOX
SUBDIRS += FrontprocessorUpgrade NFIFlash
endif

install_PYTHON =	\
	__init__.py
