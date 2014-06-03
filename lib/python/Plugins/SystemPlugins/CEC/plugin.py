#!/usr/bin/python -u
# -*- coding: UTF-8 -*-

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Plugins.Plugin import PluginDescriptor
from enigma import eTimer, evfd, eDVBVolumecontrol, iServiceInformation, eServiceCenter, eServiceReference
from time import *
from RecordTimer import *
import Screens.Standby
from ServiceReference import ServiceReference

from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList
from Components.config import config, configfile, ConfigSubsection, ConfigEnableDisable, getConfigListEntry, ConfigInteger, ConfigSelection, ConfigSelectionNumber, ConfigText
from Components.ConfigList import ConfigListScreen

from Screens.InfoBar import InfoBar

config.plugins.CEC = ConfigSubsection()
config.plugins.CEC.Enable = ConfigSelection(default = "Yes", choices = [("Yes"),("No")])
config.plugins.CEC.ActiveSource = ConfigSelection(default = "HDMI1", choices = [("HDMI1"),("HDMI2"),("HDMI3"),("HDMI4")])
config.plugins.CEC.Delay = ConfigSelectionNumber(1000, 5000, 1000, default = 1000)
config.plugins.CEC.Counter = ConfigSelectionNumber(0, 5, 1, default = 5)
config.plugins.CEC.DelayCounter = ConfigSelectionNumber(100, 1000, 100, default = 100)

CEC_Enable = "Yes"
CEC_ActiveSource = "HDMI1"
CEC_Delay = 1000
CEC_Counter = 5
CEC_DelayCounter = 100

class CECSetup(ConfigListScreen, Screen):
	skin = """
		<screen name="Konfiguracja CEC" position="center,center" size="550,400">
			<widget name="config" position="20,10" size="520,330" scrollbarMode="showOnDemand" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />

			<widget source="key_red" render="Label" position="0,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""


	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("Konfiguracja CEC")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.KeySave,
			"red": self.KeyCancel,
			"cancel": self.KeyCancel,
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.list = []
		self.list.append(getConfigListEntry(_("Interfejs aktywny"), config.plugins.CEC.Enable))
		self.list.append(getConfigListEntry(_("Aktywne wejście TV"), config.plugins.CEC.ActiveSource))
		self.list.append(getConfigListEntry(_("Opóźnienie wysłania danych [ms]"), config.plugins.CEC.Delay))
		self.list.append(getConfigListEntry(_("Powtarzaj wysyłanie danych "), config.plugins.CEC.Counter))
		self.list.append(getConfigListEntry(_("Przerwa między powtórzeniami [ms]"), config.plugins.CEC.DelayCounter))
		ConfigListScreen.__init__(self, self.list, session)

	def KeySave(self):
		print "CEC Save config"
		for x in self["config"].list:
			x[1].save()

		configfile.save()

		global CEC_Enable
		global CEC_ActiveSource
		global CEC_Delay
		global CEC_Counter
		global CEC_DelayCounter
		CEC_Enable = config.plugins.CEC.Enable.getValue()
		CEC_ActiveSource = config.plugins.CEC.ActiveSource.getValue()
		CEC_Delay = config.plugins.CEC.Delay.getValue()
		CEC_Counter = config.plugins.CEC.Counter.getValue()
		CEC_DelayCounter = config.plugins.CEC.DelayCounter.getValue()

		self.close()

	def KeyCancel(self):
		print "CEC cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close()


class CECControl:
	def __init__(self, session):
		global CEC_Enable
		global CEC_ActiveSource
		global CEC_Delay
		global CEC_Counter
		global CEC_DelayCounter
		CEC_Enable = config.plugins.CEC.Enable.getValue()
		CEC_ActiveSource = config.plugins.CEC.ActiveSource.getValue()
		CEC_Delay = config.plugins.CEC.Delay.getValue()
		CEC_Counter = config.plugins.CEC.Counter.getValue()
		CEC_DelayCounter = config.plugins.CEC.DelayCounter.getValue()
		self.licz = 0
		self.standby = 1
		self.timer = eTimer()
		self.timer.callback.append(self.timerEvent)
		self.timer.start(1000, False)
		self.timer2 = eTimer()
		self.timer2.stop()

	def CEC_Standby(self):
		global CEC_DelayCounter
		self.timer2.stop()
		self.timer2.callback.remove(self.CEC_Standby)
		#print "CEC /proc/stb/hdmi/cec Standby"
		try:
			open("/proc/stb/hdmi/cec", "w").write("3036")
		except IOError:
			print "writing /proc/stb/hdmi/cec failed"
		if self.licz>0 and self.standby==0:
			#print "CEC_DelayCounter:",CEC_DelayCounter
			self.timer2.callback.append(self.CEC_Standby)
			self.timer2.start(CEC_DelayCounter)
		self.licz=self.licz-1


	def CEC_ImageViewOn(self):
		global CEC_DelayCounter
		self.timer2.stop()
		self.timer2.callback.remove(self.CEC_ImageViewOn)
		#print "CEC /proc/stb/hdmi/cec ImageViewOn"
		try:
			open("/proc/stb/hdmi/cec", "w").write("3004")
		except IOError:
			print "writing /proc/stb/hdmi/cec failed"
#-------------------------------------------------------------------------
		if self.standby==1:
			#print "CEC_DelayCounter:",CEC_DelayCounter
			self.timer2.callback.append(self.CEC_ActiveSource)
			self.timer2.start(CEC_DelayCounter)
#-------------------------------------------------------------------------
#		if self.licz>0 and self.standby==1:
#			self.timer2.callback.append(self.CEC_ImageViewOn)
#			self.timer2.start(CEC_DelayCounter)
#		self.licz=self.licz-1
#-------------------------------------------------------------------------

	def CEC_ActiveSource(self):
		global CEC_DelayCounter
		self.timer2.stop()
		self.timer2.callback.remove(self.CEC_ActiveSource)

		global CEC_ActiveSource
		if CEC_ActiveSource=="HDMI1":
			#print "CEC /proc/stb/hdmi/cec ActiveSource-HDMI1"
			try:
				open("/proc/stb/hdmi/cec", "w").write("3f821100")
			except IOError:
				print "writing /proc/stb/hdmi/cec failed"
		if CEC_ActiveSource=="HDMI2":
			#print "CEC /proc/stb/hdmi/cec ActiveSource-HDMI2"
			try:
				open("/proc/stb/hdmi/cec", "w").write("3f822100")
			except IOError:
				print "writing /proc/stb/hdmi/cec failed"
		if CEC_ActiveSource=="HDMI3":
			#print "CEC /proc/stb/hdmi/cec ActiveSource-HDMI3"
			try:
				open("/proc/stb/hdmi/cec", "w").write("3f823100")
			except IOError:
				print "writing /proc/stb/hdmi/cec failed"
		if CEC_ActiveSource=="HDMI4":
			#print "CEC /proc/stb/hdmi/cec ActiveSource-HDMI4"
			try:
				open("/proc/stb/hdmi/cec", "w").write("3f824100")
			except IOError:
				print "writing /proc/stb/hdmi/cec failed"
		if self.licz>0 and self.standby==1:
			#print "CEC_DelayCounter:",CEC_DelayCounter
			self.timer2.callback.append(self.CEC_ImageViewOn)
			self.timer2.start(CEC_DelayCounter)
		self.licz=self.licz-1


	def timerEvent(self):
		global CEC_Delay
		global CEC_Counter
		#print "CEC_Enable=",CEC_Enable
		#print "CEC_ActiveSource=",CEC_ActiveSource

		if CEC_Enable=="Yes":
			if Screens.Standby.inStandby:
				if self.standby==1:
					self.standby = 0
					#print "CEC Box status: Standby!"
					#print "CEC_Delay:",CEC_Delay
					#print "CEC_Counter:",CEC_Counter
					self.licz = CEC_Counter
					self.timer2.callback.append(self.CEC_Standby)
					self.timer2.start(CEC_Delay)
			else:
				if self.standby==0:
					self.standby = 1
					#print "CEC Box status: Not Standby!"
					#print "CEC_Delay:",CEC_Delay
					#print "CEC_Counter:",CEC_Counter
					self.licz = CEC_Counter
					self.timer2.callback.append(self.CEC_ImageViewOn)
					self.timer2.start(CEC_Delay)

CECInstance = None

def autostart(session, **kwargs):

	global CECInstance
	if CECInstance is None:
		CECInstance = CECControl(session)

def main(session, **kwargs):
	session.open(CECSetup)

def startSetup(menuid):
	if menuid != "system":
		return []
	return [(_("Konfiguracja CEC"), main, "Konfiguracja CEC", None)]

def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), 
		PluginDescriptor(name="CEC settings", description=_("CEC settings"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]
