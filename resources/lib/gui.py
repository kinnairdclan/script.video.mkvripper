#Base imports 
import sys
import os

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

#DVD drive state codes
DRIVE_OPEN                 = 0
DRIVE_NOT_READY            = 1
DRIVE_READY                = 2
DRIVE_CLOSED_NO_MEDIA      = 3
DRIVE_CLOSED_MEDIA_PRESENT = 4
DRIVE_NONE                 = 5


#Global job
MAKEMKVCON = None

class mkvripper_gui(xbmcgui.WindowDialog):

    def gui_error(self, dialog, message):
        if dialog.ok(plugin.lang(50015), message):
            self.close()

    def __init__(self):

        global MAKEMKVCON
        dialog = xbmcgui.Dialog()
        makemkvcon_debug_on = plugin.get('makemkvcon_debug', False)

        if not makemkvcon.installed():
            plugin.log(plugin.lang(50007)) #makemkvcon binary not found

            dialog.ok(plugin.lang(50007), plugin.lang(50008), plugin.lang(50009))
            self.close()
            return

        os.putenv("XBMC_DVD_DEVICE", plugin.get('disc_number', '/dev/sr0'))
        dvdstate = xbmc.getDVDState()
        plugin.notify('DVD STATE IS: %s' % str(dvdstate)) 
        #device present error?
        if dvdstate == DRIVE_NONE:
            msg = 'No DVD drive detected on this system. Press OK to exit'
            self.gui_error(dialog, msg)
            return

        #media present error?
        elif dvdstate == DRIVE_NOT_READY:
            msg = 'DVD drive not ready. Press OK to exit'
            self.gui_error(dialog, msg)
            return
        elif dvdstate == DRIVE_OPEN:
            msg = 'DVD drive tray open. Press OK to exit'
            self.gui_error(dialog, msg)
            return
        elif dvdstate == DRIVE_CLOSED_NO_MEDIA:
            msg = 'No media detected in DVD drive. Press OK to exit'
            self.gui_error(dialog, msg)
            return
        #correct type of media error?

        job = {}
        job['dev'] = plugin.get('disc_number', '/dev/sr0') #this can be made configurable at runtime

        #device present error?

        job_running = makemkvcon.running()
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
                MAKEMKVCON = makemkvcon.start(job)
                p_dialog.create(__addonname__, plugin.lang(50005) % MAKEMKVCON['dev']) #Scanning media in <disc>
                pipe = MAKEMKVCON['output']
                label = plugin.lang(50006) % (MAKEMKVCON['dev'], MAKEMKVCON['tmp_dir']) #Ripping files from media in <disc> to temporary directory <tmp_dir>
                percent = 0
                
                while True:
                    line = pipe.stdout.readline()
                    if not line:
                        break

                    if line.startswith('MSG:'):
                        msg = line.split('"')[1]
                        if line.startswith('MSG:5038'):                                  #seems like a rather lame way to catch an error, but this is all makemkvcon's giving me
                            makemkvcon.kill(MAKEMKVCON, '-STOP')                                #pause makemkvcon
                            if dialog.yesno(__addonname__, msg):                         #display makemkvcon prompt 
                                line = ''                                                #get rid of message so progress dialog does not display it
                                makemkvcon.kill(MAKEMKVCON, '-CONT')                            #continue makemkvcon if agree
                            else:
                                sys.stdout.flush()
                                makemkvcon.kill(MAKEMKVCON)
                                MAKEMKVCON = None
                                self.close()
                                return
                        if line.startswith('MSG:5010'):
                            makemkvcon.kill(MAKEMKVCON, '-STOP')
                            msg = 'makemkvcon: %s' % msg
                            if dialog.ok(plugin.lang(50015), msg): 
                                sys.stdout.flush()
                                makemkvcon.kill(MAKEMKVCON)
                                MAKEMKVCON = None
                                self.close()
                                return
                        if line.startswith('MSG:2018'):
                            makemkvcon.kill(MAKEMKVCON, '-STOP')
                            msg = 'makemkvcon: %s' % msg
                            if dialog.ok(plugin.lang(50015), msg): 
                                sys.stdout.flush()
                                makemkvcon.kill(MAKEMKVCON)
                                MAKEMKVCON = None
                                self.close()
                                return
                        if makemkvcon_debug_on:
                            if msg.startswith('Error:'):
                                makemkvcon.kill(MAKEMKVCON, '-STOP')
                                if dialog.ok(plugin.lang(50015), msg): 
                                    sys.stdout.flush()
                                    makemkvcon.kill(MAKEMKVCON)
                                    MAKEMKVCON = None
                                    self.close()
                                    return

                    if line.startswith('PRGV:'):        
                        line = line.split(',')
                        n = float(line[1])
                        d = float(line[2])
                        percent = int(n / d * 100)


                    if p_dialog.iscanceled():
                        makemkvcon.kill(MAKEMKVCON, '-STOP')
                        if xbmcgui.Dialog().yesno(__addonname__, 'Cancel disc rip on %s?' % MAKEMKVCON['dev']):
                            makemkvcon.kill(MAKEMKVCON)
                            MAKEMKVCON = None
                            p_dialog.close()
                            self.close()
                            return
                        else:
                            makemkvcon.kill(MAKEMKVCON, '-CONT')
                            p_dialog.create(__addonname__, plugin.lang(50005) % MAKEMKVCON['dev']) #Scanning media in <disc>
                            pass

                    p_dialog.update(percent, label, msg)
                    sys.stdout.flush()

                p_dialog.update(100, plugin.lang(50016) % MAKEMKVCON['dest_writepath']) #Moving titles from temporary directory to <savedir>
                try:
                    makemkvcon.save(MAKEMKVCON)
                except Exception, e:
                    if dialog.ok(plugin.lang(50015), str(e)):
                        self.close()
                        return
                plugin.notify(plugin.lang(50013) % (MAKEMKVCON['dev'], MAKEMKVCON['dest_writepath']), timeout=10000) #Rip finished on <disc>. New files in <savedir>
                MAKEMKVCON = None
            else:
                plugin.log(plugin.lang(50010)) #User did not select a disc rip operation.
                self.close()

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or KEY_BUTTON_BACK:
            self.close()
