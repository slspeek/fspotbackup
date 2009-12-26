#!/usr/bin/env python

""" This script should take care of creating multi dvds from your f-spot
    Photos map. With the following features:
    The photos are directely visible from disc.
    Redundency is added, to ensure recovery when the disc gets damaged.
    The photo database is added to every disc.
    Staging for creation of a disc is done by hardlinking when possible.
    You can specify where to start and where to end.
    """
#TODO: genisoimage -V $JUTTERSDOK_FINAL -R -J -iso-level 4 -o jutnet-$JUTTERSDOK_FINAL.iso $BACKUP_DIR/*

import os
import sys
import commands
from os.path import join, exists, expanduser, basename, dirname, split
from os import mkdir, link
import shutil

""" Edit these values to meet yout needs
"""
# This property defines where the f-spot photo directory is
PHOTOS_DIR = '~/Photos'
# The working directory of this program (must be on same filesystem)
STAGE = '~/stage'
# This is the inclusive start date 
START_DATE = (2006, 1, 1)
# This is th incluve end date
END_DATE = (2010, 1, 1)
# This is how the prefix of your disklabel (nyi) will look (keep is short)
DISC_PREFIX = 'disc'
# The first disknumber to start with (if you have previous backups)
FIRST_DISC_NO = 1
# The redundency percentage you like
WANTED_REDUNDENCY = 14
""" Do not edit anything below this
"""

# The name of the directory on the dvds containing the redundency blocks
REDUN_DIRNAME = 'redundency'
SOFTWARE_DIR = 'f-spot-backup'
PHOTOS_DB=expanduser('~/.gnome2/f-spot/photos.db')
REDUNDENCY=WANTED_REDUNDENCY+8
DISK=4700000000
TO_BE_USED=DISK*100/(100+REDUNDENCY)
relevant_paths = []
created_discs = []

def main():
  print 'Welcome to F-spot backup in Python\n\n'
  print 'Maximum amount of bytes per disc (given ', WANTED_REDUNDENCY, '%):', TO_BE_USED
  setup_stage()
  filter_relevant_dirs()
  disc_no = 1
  disk_usage = 0
  target_path = setup_disc(disc_no)
  for path in relevant_paths:
    current_dir_size = dir_size(path)
    used_on_disc = dir_size(target_path)
    #print 'current', current_dir_size, 'used_on_disc', used_on_disc
    if (current_dir_size + used_on_disc)>TO_BE_USED:
      disc_no += 1
      target_path = setup_disc(disc_no)
    link_to_path(target_path, path)
  for disc in created_discs:
    redundency_path = join(disc, REDUN_DIRNAME)
    os.chdir(redundency_path)
    cmd = 'cd ' + redundency_path
    print cmd
    cmd = 'par2 c -b3200 -r' + `WANTED_REDUNDENCY` + ' ' + basename(disc) + ' *'  
    print cmd
    status, output = commands.getstatusoutput(cmd)
    print 'CMD status', status, 'OUTPUT', output

def copy_software(target):
  software_path = dirname(__file__)
  software_target = join(target, SOFTWARE_DIR)
  shutil.copytree(software_path, software_target)

def copy_photos_db(target):
  shutil.copy(PHOTOS_DB, target)
  photo_db_basename = basename(PHOTOS_DB)
  photo_db_ondisc = join(target, photo_db_basename)
  link(photo_db_ondisc, join(target, REDUN_DIRNAME, photo_db_basename))

def link_to_path(links_dir, link_targets_dir):
  dirs, day = os.path.split(link_targets_dir)
  dirs, month = os.path.split(dirs)
  year = basename(dirs)
  target_year = join(links_dir, year)
  if not exists(target_year):
    mkdir(target_year)
  target_month = join(target_year, month)
  if not exists(target_month):
    mkdir(target_month)
  target_day = join(target_month, day)
  if not exists(target_day):
    mkdir(target_day)
  for file in os.listdir(link_targets_dir):
    target_file = join(link_targets_dir, file)
    link_name =  join(target_day, file)
    link(target_file, link_name)
    flat_hard_link_basename = year + '___' + month + '___' + day + '___' + file 
    redundency_path = join(links_dir, '..', REDUN_DIRNAME)
    redundency_link_name = join(redundency_path, flat_hard_link_basename)
    #print link_name, redundency_link_name
    link(link_name, redundency_link_name)

def dir_size(path):
  size = 0
  status , output = commands.getstatusoutput("du -sb " + path)
  if not status:
    size = output.split()[0] 
  return int(size)

def setup_stage():
  """Sets up the stage directory where we are going the create discs from
   the photo directory
   """
  global STAGE
  STAGE = expanduser(STAGE)
  global PHOTOS_DIR
  PHOTOS_DIR = expanduser(PHOTOS_DIR)
  global PHOTOS_DIR_BASENAME 
  PHOTOS_DIR_BASENAME = basename(PHOTOS_DIR)
  if not exists(STAGE):
    mkdir(STAGE)

def setup_disc(disc_no):
  """ Sets the stage for one particular disc in this backup
      set. 
      Returns the path to copy to for this disc. 
      """
  disc_no_str = ('%03d') % (disc_no + (FIRST_DISC_NO - 1))
  disc_path = join(STAGE, DISC_PREFIX + disc_no_str)
  disc_target_path = join(disc_path, PHOTOS_DIR_BASENAME)
  redundency_path = join(disc_path, REDUN_DIRNAME)
  if not exists(disc_path):
    mkdir(disc_path)
  if not exists(disc_target_path):
    mkdir(disc_target_path)
  if not exists(redundency_path):
    mkdir(redundency_path)
  print 'Setup', disc_target_path
  created_discs.append(disc_path)
  copy_photos_db(disc_path)
  copy_software(disc_path)
  return disc_target_path


def make_path(year_str, month_str, day_str):
  """ joins its arguments prepended by the photo dir """
  path = join(PHOTOS_DIR, year_str, month_str, day_str)
  return path

def paths_for_day(year, month, day):
  """Make all different ways of spelling the directory
     whether or not zero padding could be added."""
  paths = []
  year_str = `year`
  month_str = `month`
  day_str = `day`
  paths.append(make_path(year_str, month_str, day_str))
  if month < 10:
    month_str = ('%02d') % month
    paths.append(make_path(year_str, month_str, day_str))
    if day < 10:
      day_str = ('%02d') % day
      paths.append(make_path(year_str, month_str, day_str))
      paths.append(make_path(year_str, `month`, day_str))
  elif day < 10:
    day_str = ('%02d') % day
    paths.append(make_path(year_str, month_str, day_str))
  return paths

def deal_with_possible_day(year, month, day):
  for path in paths_for_day(year, month, day):
    if exists(path):
      global relevant_paths
      relevant_paths.append(path)

def filter_relevant_dirs(start=START_DATE, end=END_DATE):
  """ Finds all possible dates (even a little more) from the 
      start to the end. """ 
  year = start[0]
  month = start[1]
  for day in range(start[2],32):
    deal_with_possible_day(year, month, day)
  for month in range(start[2]+1,13):
    for day in range(01,32):
      deal_with_possible_day(year, month, day)
  for year in range(start[0]+1, end[0]):
    for month in range(01,13):
      for day in range(01,32):
        deal_with_possible_day(year, month, day)
  year = end[0]
  for month in range(01,end[1]):
    for day in range(01,32):
      deal_with_possible_day(year, month, day)
  month = end[1]
  for day in range(01,end[2]+1):
    deal_with_possible_day(year, month, day)

if __name__ == "__main__":
      main()
