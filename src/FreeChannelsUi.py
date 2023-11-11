from os import path

from enigma import eDVBDB, eServiceCenter, eServiceReference, eTimer, iServiceInformation

from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigSelection, ConfigSubsection, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from Components.Sources.StaticText import StaticText
from Screens.ChannelSelection import ChannelSelectionBase, OFF
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from . import _


CHOICES = [(True, _("add")), (False, _("ignore")), ("top", _("top of the list"))]
FREE_BOUQUET_REF = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.freechannels.tv" ORDER BY bouquet')


config.plugins.FreeChannels = ConfigSubsection()
config.plugins.FreeChannels.delay = ConfigInteger(default=4, limits=(1, 20))
config.plugins.FreeChannels.allchannels = ConfigYesNo(default=True)
config.plugins.FreeChannels.language1 = ConfigSelection(default="top", choices=CHOICES)
config.plugins.FreeChannels.language2 = ConfigSelection(default="top", choices=CHOICES)
config.plugins.FreeChannels.language3 = ConfigSelection(default=True, choices=CHOICES)
config.plugins.FreeChannels.language4 = ConfigSelection(default=True, choices=CHOICES)


class FreeChannelsMain(ChannelSelectionBase):
	skin = """<screen position="center,center" size="655*f,470*f">
			<widget source="service" render="Label" position="15*f,10*f" size="625*f,30*f" font="Regular;25*f"/>
			<widget source="scanned_service" render="Label" position="15*f,50*f" size="625*f,30*f" font="Regular;25*f"/>
			<widget name="scan_progress" position="15*f,90*f" size="625*f,20*f"/>
			<widget name="list" position="15*f,120*f" size="625*f,280*f" enableWrapAround="1" scrollbarMode="showOnDemand" serviceItemHeight="28*f" serviceNameFont="Regular;22*f" serviceNumberFont="Regular;20*f" serviceInfoFont="Regular;15*f"/>
			<ePixmap position="15*f,415*f" size="140*f,40*f" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="blend"/>
			<widget source="key_red" render="Label" position="15*f,415*f" zPosition="2" size="140*f,40*f" valign="center" halign="center" font="Regular;20*f" transparent="1"/>
			<widget source="key_green" render="Pixmap"  position="165*f,415*f" size="140*f,40*f" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="blend">
				<convert type="ConditionalShowHide"/>
			</widget>
			<widget source="key_green" render="Label" position="165*f,415*f" zPosition="2" size="140*f,40*f" valign="center" halign="center" font="Regular;20*f" transparent="1"/>
			<widget source="key_yellow" render="Pixmap"  position="315*f,415*f" size="140*f,40*f" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="blend">
				<convert type="ConditionalShowHide"/>
			</widget>
			<widget source="key_yellow" render="Label" position="315*f,415*f" zPosition="2" size="140*f,40*f" valign="center" halign="center" font="Regular;20*f" transparent="1"/>
			<widget source="key_blue" render="Pixmap"  position="465*f,415*f" size="140*f,40*f" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="blend">
				<convert type="ConditionalShowHide"/>
			</widget>
			<widget source="key_blue" render="Label" position="465*f,415*f" zPosition="2" size="140*f,40*f" valign="center" halign="center" font="Regular;20*f" transparent="1"/>
			<ePixmap position="615*f,422*f" size="35*f,25*f" pixmap="skin_default/buttons/key_menu.png" transparent="1" alphatest="blend"/>
		</screen>"""

	def __init__(self, session):
		ChannelSelectionBase.__init__(self, session)
		self["service"] = StaticText(_("Choose where to search for free channels"))
		self["scanned_service"] = StaticText()
		self["scan_progress"] = ProgressBar()
		key_text = self["key_red"].text
		self["key_red"] = StaticText(key_text)
		key_text = self["key_green"].text
		self["key_green"] = StaticText(key_text)
		key_text = self["key_yellow"].text
		self["key_yellow"] = StaticText(key_text)
		key_text = self["key_blue"].text
		self["key_blue"] = StaticText(key_text)
		self["actions"] = ActionMap(["OkCancelActions", "ChannelSelectBaseActions", "MenuActions"], {
			"ok": self.ok_selected,
			"cancel": self.cancel_selected,
			"showAllServices": self.showAllServices,
			"showSatellites": self.showSatellites,
			"showProviders": self.showProviders,
			"showFavourites": self.showFavourites,
			"menu": self.open_menu})
		self.onLayoutFinish.append(self.layout_finish)
		self.onClose.append(self.on_exit)
		self.bouquet_mark_edit = OFF
		self.delay_timer = eTimer()
		self.delay_timer.timeout.callback.append(self.get_info)
		self.services_list = None
		self.services_count = 0
		self.top_pos = 0

	def layout_finish(self):
		self.setTvMode()
		self.showFavourites()

	def on_exit(self):
		self.delay_timer.stop()

	def showAllServices(self):
		if not self.services_list:
			ChannelSelectionBase.showAllServices(self)
		else:
			self.cancel_selected()

	def showSatellites(self, changeMode=True):
		if not self.services_list:
			ChannelSelectionBase.showSatellites(self, changeMode)

	def showProviders(self):
		if not self.services_list:
			ChannelSelectionBase.showProviders(self)

	def showFavourites(self):
		if not self.services_list:
			ChannelSelectionBase.showFavourites(self)

	def open_menu(self):
		self.session.open(FreeChannelsSetup)

	def cancel_selected(self):
		if not self.services_list or self.services_count == -1:
			self.close()
		else:
			self.session.openWithCallback(self.cancel_scan, MessageBox, _("Stop search?"), MessageBox.TYPE_YESNO)

	def cancel_scan(self, answer):
		self.delay_timer.stop()
		if answer:
			self.zap_service(True)
		else:
			self.delay_timer.start(config.plugins.FreeChannels.delay.value * 1000, True)

	@staticmethod
	def get_services(ref):
		services = []
		servicelist = eServiceCenter.getInstance().list(ref)
		if servicelist:
			while True:
				service = servicelist.getNext()
				if not service.valid():
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
					continue
				name = eServiceCenter.getInstance().info(service).getName(service)
				if not name or name == ".":
					continue
				for n in (" SID 0X", "(...)", "TEST ", " TEST"):
					if n in name.upper():
						break
				else:
					services.append((name, service))
		if "ORDER BY bouquet" not in ref.toString():
			services.sort(key=lambda x: x[0])
		return [s[1] for s in services]

	def get_services_list(self):
		services = self.get_services(self.cur_root)
		self.services_count = len(services)
		self["scan_progress"].range = (0, self.services_count)
		services.append(None)  # Marks the end of the list
		i = 0
		for service in services:
			i += 1
			yield i, service

	def zap_service(self, stop=False):
		try:
			i, service = next(self.services_list)
		except StopIteration:  # I don"t know why this error sometimes happens
			service = None
		if service and not stop:
			self["service"].text = "%s - %s" % (_("%d of %d") % (i, self.services_count), eServiceCenter.getInstance().info(service).getName(service))
			self["scan_progress"].value = i
			self.session.nav.playService(service, checkParentalControl=False)
			self.delay_timer.start(config.plugins.FreeChannels.delay.value * 1000, True)
		else:
			self["service"].text = _("Search complete")
			self["scanned_service"].text = ""
			self.services_count = -1  # Marks search complete

	@staticmethod
	def check_languages(lang):
		top_lang = []
		bottom_lang = []

		def set_language(autoselect, lang_choice):
			if autoselect:
				if lang_choice == "top":
					top_lang.extend(autoselect.split())
				elif lang_choice:
					bottom_lang.extend(autoselect.split())

		set_language(
			config.autolanguage.audio_autoselect1.value,
			config.plugins.FreeChannels.language1.value,
		)
		set_language(
			config.autolanguage.audio_autoselect2.value,
			config.plugins.FreeChannels.language2.value,
		)
		set_language(
			config.autolanguage.audio_autoselect3.value,
			config.plugins.FreeChannels.language3.value,
		)
		set_language(
			config.autolanguage.audio_autoselect4.value,
			config.plugins.FreeChannels.language4.value,
		)

		def is_language(languages):
			for x in languages:
				if x in lang:
					break
			else:
				return False
			return True

		lang_value = is_language(top_lang) and "top" or False
		if not lang_value:
			lang_value = is_language(bottom_lang)

		return lang_value

	def get_info(self):
		service = self.session.nav.getCurrentService()
		if service:
			info = service.info()
			if info:
				sinfo = info.getInfo(iServiceInformation.sIsCrypted) and _("Crypted") or _("Free")
				lang = []
				lang_value = config.plugins.FreeChannels.allchannels.value
				audio = service.audioTracks()
				if audio:
					for x in range(audio.getNumberOfTracks()):
						lang.extend(audio.getTrackInfo(x).getLanguage().split("/"))
				if not lang:
					sinfo += _(", no audio")
				elif not lang_value:
					lang_value = self.check_languages(lang)
					if not lang_value:
						lang = []
				self["scanned_service"].text = "%s - %s" % (info.getName(), sinfo)
				if sinfo == _("Free") and lang:
					servicelist = eServiceCenter.getInstance().list(FREE_BOUQUET_REF).startEdit()
					if servicelist:
						ref = self.session.nav.getCurrentlyPlayingServiceReference()
						servicelist.addService(ref)
						if lang_value == "top":
							servicelist.moveService(ref, self.top_pos)
						servicelist.flushChanges()
						self.enterPath(FREE_BOUQUET_REF)
						if lang_value == "top":
							self.servicelist.instance.moveSelectionTo(self.top_pos)
							self.top_pos += 1
						else:
							self.servicelist.instance.moveSelection(self.servicelist.instance.moveEnd)
		self.zap_service()

	def ok_selected(self):
		ref = self.getCurrentSelection()
		if ref.type == -1:
			return
		if not self.services_list:
			if (ref.flags & eServiceReference.flagDirectory) == eServiceReference.flagDirectory:
				self.enterPath(ref)
			elif not ref.flags & eServiceReference.isMarker:
				self.cur_root = self.getRoot()
				if self.cur_root:
					self.session.openWithCallback(self.start_scan, MessageBox, _("Start searching for free channels in this bouquet?"), MessageBox.TYPE_YESNO)
		elif self.services_count == -1:
			cur_ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			if not cur_ref or cur_ref != ref:
				self.session.nav.playService(ref)
			self.close()

	def start_scan(self, answer):
		if answer:
			self.title = _("Search for free channels")
			self["key_red"].text = _("Exit")
			self["key_green"].text = ""
			self["key_yellow"].text = ""
			self["key_blue"].text = ""
			self.services_list = self.get_services_list()
			if path.isfile("/etc/enigma2/userbouquet.freechannels.tv"):
				self.session.openWithCallback(self.remove_services, MessageBox, _("Delete all existing channels from the free channel bouquet before searching?"), MessageBox.TYPE_YESNO, default=False)
			else:
				self.create_bouquet()

	def create_bouquet(self):
		service_instance = eServiceCenter.getInstance()
		new_bouquet = service_instance.list(self.bouquet_root).startEdit()
		if not new_bouquet.addService(FREE_BOUQUET_REF):
			new_bouquet.flushChanges()
			eDVBDB.getInstance().reloadBouquets()
			new_bouquet = service_instance.list(FREE_BOUQUET_REF).startEdit()
			if new_bouquet:
				# TRANSLATORS: Bouquet name in channel list
				new_bouquet.setListName(_("Free channels"))
				new_bouquet.flushChanges()
				self.enterPath(FREE_BOUQUET_REF)
				self.zap_service()

	def remove_services(self, answer):
		if answer:
			self.enterPath(FREE_BOUQUET_REF)
			servicelist = eServiceCenter.getInstance().list(FREE_BOUQUET_REF).startEdit()
			if servicelist:
				while True:
					ref = self.servicelist.getCurrent()
					if not ref.valid():
						break
					if not servicelist.removeService(ref):
						self.servicelist.removeCurrent()
				servicelist.flushChanges()
		self.enterPath(FREE_BOUQUET_REF)
		self.zap_service()


class FreeChannelsSetup(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("Setup")
		self.session = session
		self.skinName = ["FreeChannelsSetup", "Setup"]
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["description"] = Label()
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"ok": self.keySave,
			"green": self.keySave})
		ConfigListScreen.__init__(self, [], session=session)
		config.plugins.FreeChannels.allchannels.addNotifier(self.update_configlist, initial_call=False)
		self.update_configlist()

	def update_configlist(self, config_element=None):
		if "config" not in self:
			return
		config_list = [
			(_("Channel tuning time"), config.plugins.FreeChannels.delay,
				_("Time in seconds to tune to a channel.\nIf the time is shorter, the channel search will be faster, but the information will not be correct.")),
			(_("Add channels in any language"), config.plugins.FreeChannels.allchannels,
				_("Adds all channels to the list regardless of the languages in which they are available."))
		]
		if not config.plugins.FreeChannels.allchannels.value:
			lang_choices = {  # audio_language_choices in https://github.com/OpenPLi/enigma2/blob/develop/lib/python/Components/UsageConfig.py
				"orj dos ory org esl qaa qaf und mis mul ORY ORJ Audio_ORJ oth": _("Original"),
				"ara": _("Arabic"),
				"eus baq": _("Basque"),
				"bul": _("Bulgarian"),
				"hrv": _("Croatian"),
				"chn sgp": _("Chinese - Simplified"),
				"twn hkn": _("Chinese - Traditional"),
				"ces cze": _("Czech"),
				"dan": _("Danish"),
				"dut ndl nld": _("Dutch"),
				"eng": _("English"),
				"est": _("Estonian"),
				"fin": _("Finnish"),
				"fra fre": _("French"),
				"deu ger": _("German"),
				"ell gre grc": _("Greek"),
				"heb": _("Hebrew"),
				"hun": _("Hungarian"),
				"ind": _("Indonesian"),
				"ita": _("Italian"),
				"lav": _("Latvian"),
				"lit": _("Lithuanian"),
				"ltz": _("Luxembourgish"),
				"nor": _("Norwegian"),
				"fas per fa pes": _("Persian"),
				"pol": _("Polish"),
				"por dub Dub DUB ud1": _("Portuguese"),
				"ron rum": _("Romanian"),
				"rus": _("Russian"),
				"srp": _("Serbian"),
				"slk slo": _("Slovak"),
				"slv": _("Slovenian"),
				"spa": _("Spanish"),
				"swe": _("Swedish"),
				"tha": _("Thai"),
				"tur Audio_TUR": _("Turkish"),
				"ukr Ukr": _("Ukrainian"),
				"NAR qad": _("Visually impaired"),
			}

			def get_lang(conf):
				lang = conf.value
				if lang in lang_choices:
					return lang_choices[lang]
				return lang

			SETTINGS = _("Channels in %s")
			DESCRIPTION = _("You can add channels that contain the specified language to the top of the list, to the bottom of the list, or ignore and not add to the list.\nYou can specify the language in the auto language selection settings.")

			if config.autolanguage.audio_autoselect1.value:
				config_list.append((
					SETTINGS % get_lang(config.autolanguage.audio_autoselect1),
					config.plugins.FreeChannels.language1,
					DESCRIPTION
				))
			if config.autolanguage.audio_autoselect2.value:
				config_list.append((
					SETTINGS % get_lang(config.autolanguage.audio_autoselect2),
					config.plugins.FreeChannels.language2,
					DESCRIPTION
				))
			if config.autolanguage.audio_autoselect3.value:
				config_list.append((
					SETTINGS % get_lang(config.autolanguage.audio_autoselect3),
					config.plugins.FreeChannels.language3,
					DESCRIPTION
				))
			if config.autolanguage.audio_autoselect4.value:
				config_list.append((
					SETTINGS % get_lang(config.autolanguage.audio_autoselect4),
					config.plugins.FreeChannels.language4,
					DESCRIPTION
				))
		self["config"].list = config_list
