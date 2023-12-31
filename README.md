[![](https://img.shields.io/badge/License-GPLv3-green.svg)](https://github.com/Taapat/enigma2-plugin-freechannels/blob/master/LICENSE)  [![](https://sonarcloud.io/api/project_badges/measure?project=Taapat_enigma2-plugin-freechannels&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Taapat_enigma2-plugin-freechannels)  [![](https://img.shields.io/github/downloads/Taapat/enigma2-plugin-freechannels/total)](https://github.com/Taapat/enigma2-plugin-freechannels/releases)  [![](https://img.shields.io/github/v/release/Taapat/enigma2-plugin-freechannels)](https://github.com/Taapat/enigma2-plugin-freechannels/releases)
-------
Enigma2 plugin Free channels
=========
Scan bouquets to find FTA (free-to-air) channels and add to the bouquet if it contains the specified language.

You can scan all channels, satellites, providers or user bouquets.

The plugin creates a separate bouquet "Free channels" in which it stores the found channels.

The plugin switches channels one by one and tunes them specified time, to get information about audio tracks and crypted status.
You can set the time in seconds to tune to a channel. If the time is shorter, the channel search will be faster, but the information will not be correct.

You can choose or add channels in any language, or channels that contain the specified language to the top of the list, to the bottom of the list, or ignore and not add to the list.
You can specify the languages in the image auto language selection settings.

Plugin embedded skin uses scaling and svg, therefore will work on OpenPLi images starting from version 8.1.

[Example of BitBake file](https://github.com/OpenPLi/openpli-oe-core/blob/develop/meta-openpli/recipes-openpli/enigma2-plugins/enigma2-plugin-extensions-freechannels.bb)


Download
-------
Packages with py3 in the version name are for Python3, with py2 for Python2.

[Plugin Free channels latest release](https://github.com/Taapat/enigma2-plugin-freechannels/releases/latest)

Screenshots
-------
![](https://user-images.githubusercontent.com/1623947/282240641-7777505d-6fac-402d-9cfd-a228428ae9ac.jpg)

![](https://user-images.githubusercontent.com/1623947/282240645-2aa87120-9788-4044-8e25-e27df5fa36e2.jpg)

![](https://user-images.githubusercontent.com/1623947/282240665-4c1eb11f-6c14-4b3e-8eec-2043c08c844d.jpg)

![](https://user-images.githubusercontent.com/1623947/283177263-b9044cc2-7da7-443e-8f69-435a67060460.jpg)

![](https://user-images.githubusercontent.com/1623947/283174747-7f294adf-6612-4562-bd83-690b160137d4.jpg)

![](https://user-images.githubusercontent.com/1623947/283174785-a02032f8-e06a-464c-904d-b866a31e1a94.jpg)
