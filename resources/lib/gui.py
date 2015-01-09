#Base imports 
import sys

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
KEY_BUTTON_BACK = 275

class mkvripper_gui(xbmcgui.WindowDialog):

    def __init__(self):

        dialog = xbmcgui.Dialog()

        if not makemkvcon.installed():
            plugin.log(plugin.lang(50007)) #makemkvcon binary not found

            dialog.ok(plugin.lang(50007), 
                      plugin.lang(50008),
                      plugin.lang(50009))
            self.close()
            return

        #media present error?
        #correct type of media error?
        #RIP FROM WHERE menu: this should react with makemkv's file option...maybe let's think about this

        job = {}
        job['dev'] = plugin.get('disc_number', '/dev/sr0') #this can be made configurable at runtime

        #device present error?

        job_running = makemkvcon.running(job['dev'])
        if job_running:
            label = xbmcgui.ControlLabel(100, 120, 200, 200, plugin.lang(50012) % job['dev']) #Rip operation already running on <disc>
            button0 = xbmcgui.ControlButton(350, 500, 80, 30, 'derp')
            addControls(self, self.label, self.button0)

        else:
            starting = dialog.yesno(__addonname__, plugin.lang(50011) % job['dev']) #Rip media from disc on <disc>?
            if starting:
                job['dest_writepath'] = dialog.browse(3, plugin.lang(51001), 'video', '', False, False, '')
                if job['dest_writepath'] == '':
                    self.close()
                    return

                kb = xbmc.Keyboard('', plugin.lang(51002)) 
                kb.doModal()
                if kb.isConfirmed():
                    job['dest_savename'] = kb.getText()
                    if job['dest_savename'] == '':
                        job['dest_savename'] = plugin.lang(51003) #title.mkv for single file or titleXX.mkv for multiple files are default savenames
                else:
                    self.close()
                    return

                p_dialog = xbmcgui.DialogProgress() #here you might want to roll a special progress window that shelves the job onto service and wakes up service 
                p_dialog.create(__addonname__, plugin.lang(50005) % job['dev']) #Scanning media in <disc>
                job = makemkvcon.start(job)
                pipe = job['output']
                msg = plugin.lang(50006) #Ripping files from media in <disc>

                while True:
                    line = pipe.stdout.readline()
                    if not line:
                        break
                    if line.startswith('MSG:'):
                        p_dialog.update(0, msg % job['dev'], line.split('"')[1])
                        sys.stdout.flush()
                    if p_dialog.iscanceled():
                        makemkvcon.kill(job)
                        plugin.notify(plugin.lang(50014) % job['dev'])
                        return
                makemkvcon.save(job)
                plugin.notify(plugin.lang(50013) % job['dev'])
            else:
                plugin.log(plugin.lang(50010)) #User did not select a disc rip operation.
                self.close()

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or KEY_BUTTON_BACK:
            self.close()
            pass
