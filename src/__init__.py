import gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


def locale_init():
	gettext.bindtextdomain(
		"FreeChannels",
		resolveFilename(SCOPE_PLUGINS, "Extensions/FreeChannels/locale")
	)


def _(txt):
	t = gettext.dgettext("FreeChannels", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


locale_init()
language.addCallback(locale_init)
