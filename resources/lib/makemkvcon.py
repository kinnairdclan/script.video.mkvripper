# Base imports
import os
import shutil
import tempfile
import subprocess

# XBMC imports
import xbmc
import xbmcaddon
import xbmcgui

# Local imports
import plugin

# Addon info
__addon__     = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')

def installed():
    path = plugin.get('makemkvcon_path', 'makemkvcon')
    plugin.log('makemkvcon_path = %s' % path)
    try:
        p = subprocess.Popen(path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p = None
        return True
    except Exception, e:
        plugin.log(plugin.lang(50017) % e.strerror) #makemkvcon.installed() ERROR: %s
    return False

def running(dev=None):
    import glob
    path = plugin.get('makemkvcon_path', 'makemkvcon')
    for f in glob.glob('/proc/*/cmdline'):
        try:
            cl = open(f).read()
            if cl.startswith(path):
                if dev is None:
                    return f.split('/')[2] #pid of running makemkvcon
                else:
                    if dev in cl:
                        return f.split('/')[2] #pid of running makemkvcon corresponding to dev
        except Exception, e:
            raise
    return 0

def cleanup(job):
    tmp_dir = job['tmp_dir']
    try:
        shutil.rmtree(tmp_dir)
    except Exception, e:
        plugin.log(plugin.lang(50018) % e.strerror) #makemkvcon.cleanup() ERROR: %s
    #remove job from service 
    #zero out elements of job if applicable here -- not necessary yo.

def kill(job, signal='-KILL'):
    pid = str(job['pid'])
    plugin.log(plugin.lang(50019) % (job['dev'], signal)) #killing makemkvcon job on %s with signal %s
    cmd = ['kill', signal, pid]
    subprocess.call(cmd)
    if signal == '-KILL':
        if job['tmp_dir'] is not None:
            cleanup(job)

def start(job):

    job['tmp_dir'] = tempfile.mkdtemp(suffix='.mkvripper', dir=job['dest_writepath'])

    ripsize_min = plugin.get('ripsize_min', '600')

    cmd = plugin.get('makemkvcon_path', 'makemkvcon')
    cmd = [cmd, '-r', '--progress=-stdout', '--minlength=%s' % ripsize_min, 
           'mkv', 'dev:%s' % job['dev'], 'all', job['tmp_dir']]
    job['cmd'] = cmd
    job['output'] = subprocess.Popen(job['cmd'], 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    close_fds=True)

    job['pid'] = job['output'].pid
    plugin.log(plugin.lang(50021) % job['cmd']) #started new makemkvcon with command %s
    return job

def save(job):

#Special exception for save(): is temporary directory empty after a rip? If so, error could be a multitude of things...makemkvcon likes to exit successfully with zero files ripped sometimes.
	class TmpDirEmpty(Exception):
		def __init__(self, message):
			super(TmpDirEmpty, self).__init__(message)
			self.message = message

    if not running():
        l = os.listdir(job['tmp_dir'])
		if l == []:
            cleanup(job)
			raise TmpDirEmpty('temporary directory empty!')
        for i in l:

            src = os.path.join(job['tmp_dir'], i)
            if len(l) >= 2:
                dest = os.path.join(job['dest_writepath'], job['dest_savename'] + i[-6:]) #save as numbered .mkv file if there is more than one file to be saved
            else:
                dest = os.path.join(job['dest_writepath'], job['dest_savename'] + i[-4:]) #save without numbered suffix if only one .mkv file to be saved

            try:
                shutil.move(src, dest)
            except Exception, e:
                plugin.log(plugin.lang(50022) % e.strerror) #makemkvcon.save() ERROR: %s
                cleanup(job)
                raise
        cleanup(job)
