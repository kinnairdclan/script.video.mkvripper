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

#Global job
MAKEMKVCON = None

class mkvripper_gui(xbmcgui.WindowDialog):

    def __init__(self):

        global MAKEMKVCON
        dialog = xbmcgui.Dialog()

        if not makemkvcon.installed():
            plugin.log(plugin.lang(50008)) #makemkvcon binary not found

            if dialog.ok(plugin.lang(50015), plugin.lang(50008)): #makemkvcon binary not found. Install MakeMKV or adjust makemkvcon binary path setting.
                self.close()
                return

        job = {}
        job['dev'] = plugin.get('disc_number', '/dev/sr0') #configurable in settings

        starting = dialog.yesno(__addonname__, plugin.lang(50011) % job['dev']) #Rip media from disc on <disc>?
        if starting:

            #is cdrom Device?
            info = open('/proc/sys/dev/cdrom/info').read()
            dev = job['dev'].split('/')[-1] 
            if dev not in info:
                if dialog.ok(plugin.lang(50015), plugin.lang(50002)): #Disc drive device file not reported as CDROM device. Adjust disc drive device file setting.
                    self.close()
                    return

            job_running = makemkvcon.running(job['dev'])

            if job_running:
                if dialog.yesno(__addonname__, plugin.lang(50012) % job['dev'], nolabel=plugin.lang(52001), yeslabel=plugin.lang(52002)): #Rip operation already running on <disc>. Cancel running operation and start over or exit?
                    job['pid'] = job_running
                    makemkvcon.kill(job)
                else:
                    plugin.log(plugin.lang(50010)) #User did not select a disc rip operation.
                    self.close()
                    return

            while True:
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
                    break

            p_dialog = xbmcgui.DialogProgress()
            MAKEMKVCON = makemkvcon.start(job)
            p_dialog.create(__addonname__, plugin.lang(50005) % MAKEMKVCON['dev']) #Scanning media in <disc>
            pipe = MAKEMKVCON['output']
            label = plugin.lang(50006) % MAKEMKVCON['dev'] #Ripping files from media in <disc>
            percent = 0
            
            while True:
                line = pipe.stdout.readline()
                if not line:
                    break

                if line.startswith('MSG:'):
                    msg = line.split('"')[1]
                    if line.startswith('MSG:5038'):        #Disc space error; is a prompt.
                        makemkvcon.kill(MAKEMKVCON, '-STOP')
                        if dialog.yesno(__addonname__, msg):
                            line = ''      
                            makemkvcon.kill(MAKEMKVCON, '-CONT')
                        else:
                            sys.stdout.flush()
                            makemkvcon.kill(MAKEMKVCON)
                            MAKEMKVCON = None
                            self.close()
                            return
                    if line.startswith('MSG:5010'):         #Failed to open disc error. Can stem from a number of things such as tray status and inserted media type.
                        makemkvcon.kill(MAKEMKVCON, '-STOP')
                        msg = 'makemkvcon: %s %s' % (msg, plugin.lang(50004)) #Failed to open disc, ensure correct media inserted and device tray closed.
                        if dialog.ok(plugin.lang(50015), msg): 
                            sys.stdout.flush()
                            makemkvcon.kill(MAKEMKVCON)
                            MAKEMKVCON = None
                            self.close()
                            return
                    if msg.startswith('Error'):             #Kind of a lame way to catch an error, but reading makemkvcon's output works for HDD space issues as well as tray issues.
                        makemkvcon.kill(MAKEMKVCON, '-STOP')
                        msg = 'makemkvcon: %s' % msg
                        if dialog.ok(plugin.lang(50015), msg): 
                            sys.stdout.flush()
                            makemkvcon.kill(MAKEMKVCON)
                            MAKEMKVCON = None
                            self.close()
                            return

                if line.startswith('PRGV:'):        #Monitor rip progress for progress bar
                    line = line.split(',')
                    n = float(line[1])
                    d = float(line[2])
                    percent = int(n / d * 100)

                if p_dialog.iscanceled():
                    makemkvcon.kill(MAKEMKVCON, '-STOP')
                    if dialog.yesno(__addonname__, plugin.lang(50003) % MAKEMKVCON['dev']): #Cancel rip operation on <disc>?
                        makemkvcon.kill(MAKEMKVCON)
                        MAKEMKVCON = None
                        p_dialog.close()
                        self.close()
                        return
                    else:
                        makemkvcon.kill(MAKEMKVCON, '-CONT')
                        p_dialog.create(__addonname__, plugin.lang(50005) % MAKEMKVCON['dev']) #Scanning media in <disc>

                p_dialog.update(percent, label, msg)
                sys.stdout.flush()

            p_dialog.update(100, plugin.lang(50016) % MAKEMKVCON['dest_writepath']) #Moving titles from temporary directory to <savedir>
            try:
                makemkvcon.save(MAKEMKVCON)
            except makemkvcon.TmpDirEmpty:				#Is temporary directory empty after rip has completed successfully?
		if dialog.ok(plugin.lang(50015), plugin.lang(50023)): 	#Plugin detected that makemkvcon ripped no files but exited successfully.
                    self.close()
                    return
            except Exception, e:								#some other error with shutil.move()
                if dialog.ok(plugin.lang(50015), e.strerror):
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
