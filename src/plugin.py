from Plugins.Plugin import PluginDescriptor

from . import _


def main(session, **kwargs):
	from .FreeChannelsUi import FreeChannelsMain
	session.open(FreeChannelsMain)


def Plugins(**kwargs):
	return [PluginDescriptor(
		name=_("Find free channels"),
		description=_("Scan bouquets to find free channels"),
		where=[PluginDescriptor.WHERE_PLUGINMENU],
		icon="FreeChannels.svg",
		fnc=main)]
