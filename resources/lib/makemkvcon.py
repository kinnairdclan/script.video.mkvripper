# Base imports
import os
import shutil
import sys
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

#
# Check if binary is installed
#

def installed():
    path = plugin.get('makemkvcon_path', 'makemkvcon')
    plugin.log('makemkvcon_path = %s' % path)
    try:
        p = subprocess.Popen(path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p = None
        return True
    except Exception, e:
        plugin.log('makemkvcon.installed() ERROR: %s' % e)
    return False

def running(dev):
    import glob
    path = plugin.get('makemkvcon_path', '/usr/bin/makemkvcon')
    for f in glob.glob('/proc/*/cmdline'):
        try:
            cl = open(f).read()
            if cl.startswith(path):
                if dev in cl:
                    return True
        except: pass
    return False

def cleanup(job):
    tmp_dir = job['tmp_dir']
    try:
        shutil.rmtree(tmp_dir)
    except IOError, e:
        plugin.log('makemkvcon.cleanup() ERROR: %s' % e)
    #remove job from service 
    #zero out elements of job if applicable here

def kill(job):
    pid = str(job['pid'])
    plugin.log('killing makemkvcon job on %s' % job['dev'])
    cmd = ['kill', pid]
    subprocess.call(cmd)
    cleanup(job)

def start(job):
    job['tmp_dir'] = tempfile.mkdtemp()
    if running(job['dev']):
        plugin.log('makemkvcon already running on %s' % job['dev'])
        return

    ripsize_min = plugin.get('ripsize_min', '600')
    disc_number = plugin.get('disc_number', '/dev/sr0')

    cmd = plugin.get('makemkvcon_path', '/usr/bin/makemkvcon')
    cmd = [cmd, '-r', '--minlength=' + ripsize_min, 'mkv', 'dev:' + disc_number, 'all', job['tmp_dir']]
    job['cmd'] = cmd
    job['dev'] = disc_number
    plugin.log("FULL COMMAND IS: ")
    plugin.log(str(cmd))
    job['output'] = subprocess.Popen(job['cmd'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    job['pid'] = job['output'].pid
    plugin.log('started new makemkvcon') 
    return job

def save(job):
    if not running(job['dev']):
        l = os.listdir(job['tmp_dir'])
        for i in l:

            src = os.path.join(job['tmp_dir'], i)
            if len(l) >= 2:
                dest = os.path.join(job['dest_writepath'], job['dest_savename'] + i[-6:]) #save as numbered .mkv file if there is more than one file to be saved
            else:
                dest = os.path.join(job['dest_writepath'], job['dest_savename'] + i[-4:]) #save without numbered suffix if only one .mkv file to be saved

            try:
                shutil.move(src, dest)
            except IOError, e:
                plugin.log('makemkvcon.save() ERROR: %s' % e)
                cleanup(job)
        cleanup(job)
                

