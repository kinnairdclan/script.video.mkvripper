# XBMC imports
import xbmc
import xbmcaddon
import xbmcgui

# Local imports
import makemkvcon
import plugin

__addon__     = xbmcaddon.Addon()
__cwd__       = __addon__.getAddonInfo('path')
__addonname__ = __addon__.getAddonInfo('name')

ACTION_PREVIOUS_MENU = 10

class mkvripper_gui(xbmcgui.WindowDialog):

    def __init__(self):

        job = {}
        job['dev'] = plugin.get('disc_number', '/dev/sr0')

        job_running = makemkvcon.running(job['dev'])
        #if job_running:
        #    label = xbmcgui.ControlLabel(100, 120, 200, 200, 'Rip operation already running on %s' % job['dev'])
        #    button0 = xbmcgui.ControlButton(350, 500, 80, 30, 'derp')
        #    addControls(self, self.label, self.button0)
        #else:
        starting = xbmcgui.Dialog().yesno(__addonname__, 'Rip on disc:%s?' % job['dev'])
        if starting:
            plugin.log('said yes!')
            self.close
        else:
            plugin.log('said no!')
            self.close()

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU:
            self.close()
