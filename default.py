#Base imports
import os
import sys

#Kodi imports
import xbmc
import xbmcaddon

#Local imports
__addon__ = xbmcaddon.Addon()
__cwd__ = __addon__.getAddonInfo('path')

BASE_RESOURCE_PATH = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))
sys.path.append(BASE_RESOURCE_PATH)

if __name__ == '__main__':
    import plugin
    from gui import mkvripper_gui
    w = mkvripper_gui()
    del w
