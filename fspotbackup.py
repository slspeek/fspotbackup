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
from datetime import date, timedelta

""" Edit these values to meet yout needs
"""
# This property defines where the f-spot photo directory is
PHOTOS_DIR = expanduser('~/Photos')
# The working directory of this program (must be on same filesystem)
STAGE = expanduser('~/stage')
# This is the inclusive start date 
START_DATE = (2006, 1, 1)
# This is th incluve end date
END_DATE = (2010, 1, 1)
# This is how the prefix of your disklabel (nyi) will look (keep is short)
DISC_PREFIX = 'disc'
# The first disknumber to start with (if you have previous backups)
FIRST_DISC_NO = 1
# The redundancy percentage you like
WANTED_REDUNDANCY = 14
""" Do not edit anything below this
"""

# The name of the directory on the dvds containing the redundancy blocks
REDUN_DIRNAME = 'redundancy'
SOFTWARE_DIR = 'fspotbackup'
FILELIST_POSTFIX = '_file.list'
REPAIR_SCRIPT = 'par2repair.sh'
CREATE_PAR2_SCRIPT = 'par2create.sh'
VERIFY_SCRIPT = 'par2verify.sh'
CREATE_LINKS_SCRIPT = 'create_links.sh'
REMOVE_LINKS_SCRIPT = 'remove_links.sh'
CREATE_ISO_SCRIPT = 'create_iso_image.sh'
SCRIPTS_DIR = 'scripts'
PHOTOS_DB=expanduser('~/.gnome2/f-spot/photos.db')
REDUNDANCY=WANTED_REDUNDANCY+8
DISK=4700000000
TO_BE_USED=DISK*100/(100+REDUNDANCY)
LINK_SEPARATOR='___'

relevant_days = []
created_discs = []

class Disc(object):
  """ One medium volume """
  def __init__(self, disc_no):
      self.disc_no = disc_no
      self.days = []
      self.size = 0

  def size(self):
    return self.size

  def setup_disc(self):
    """ Sets the stage for one particular disc in this backup
        set. Returns the path to copy to for this disc. 
        """
    disc_no_str = ('%03d') % (self.disc_no + (FIRST_DISC_NO - 1))
    self.disc = DISC_PREFIX + disc_no_str
    self.disc_path = join(STAGE, self.disc)
    self.disc_target_path = join(self.disc_path, PHOTOS_DIR_BASENAME)
    self.redundancy_path = join(self.disc_path, REDUN_DIRNAME)
    if not exists(self.disc_target_path):
      os.makedirs(self.disc_target_path)
    if not exists(self.redundancy_path):
      mkdir(self.redundancy_path)
    print 'Setup', self.disc
    created_discs.append(self)
    self.copy_photos_db()
    self.copy_software()
    return self.disc_target_path

  def add(self, day):
    self.days.append(day)
    self.size += day.size

  def copy_software(self):
    software_path = dirname(__file__)
    software_target = join(self.disc_path, SOFTWARE_DIR)
    shutil.copytree(software_path, software_target)

  def copy_photos_db(self):
    shutil.copy(PHOTOS_DB, self.disc_path)
    photo_db_basename = basename(PHOTOS_DB)
    photo_db_ondisc = join(self.disc_path, photo_db_basename)
    link(photo_db_ondisc, join(self.disc_path, REDUN_DIRNAME, photo_db_basename))

  def create_par2create_script(self):
    cmd = 'par2 c -b3200 -r' + `WANTED_REDUNDANCY` + ' ' + basename(disc) + ' *'  
    print cmd
  
  def create_par2verify_script(self):
    content = 'cd ../' + REDUN_DIRNAME + ' && ' 
    content += 'par2 v ' + self.disc + '.par2\n'  
    write_script(self, CREATE_PAR2_SCRIPT, content)

  def create_par2repair_script(self):
    pass

  def create_link_removal_script(self):
    pass

  def write_script(self, script_name, content):
    pass

  def create_filelist(self):
    file_list = open(join(self.disc_path, self.disc + FILELIST_POSTFIX), 'w')
    for day in self.days:
      for file in day.files:
        file_list.write(file.ondisc_path(self) + ' (' + file.source_path() + ')\n')
    file_list.close()
    pass


class Day(object):
  """ Respresents one file to be backed up """
  def __init__(self, year, month, day):
    self.year = year
    self.month = month
    self.day = day
    self.files = []
    self.size = 0

  def make_links(self, disc):
    for file in self.files:
      file.link(disc)

  def scan(self):
    for filename in os.listdir(self.source_path()):
      file = File(self.year, self.month, self.day, filename)
      self.files.append(file)
      self.size += file.get_size()

  def source_path(self):
    path = join(PHOTOS_DIR,
                self.year,
                self.month,
                self.day)
    return path

  def target_path(self, disc):
    path = join(disc.disc_target_path,
    self.year, 
    self.month, 
    self.day)
    return path
  
  def make_dir(self, disc):
    os.makedirs(join(disc.disc_target_path, self.year, self.month, self.day))

class File(Day):
  def __init__(self, year, month, day, filename):
    Day.__init__(self, year, month, day)
    self.filename = filename

  def source_path(self):
    return join(Day.source_path(self), self.filename)

  def target_path(self, disc):
    return join(Day.target_path(self, disc), self.filename)

  def ondisc_path(self, disc):
    return join(PHOTOS_DIR_BASENAME, self.year, self.month, self.day, self.filename)

  def link(self, disc):
    link(self.source_path(), self.target_path(disc))

  def redundancy_path(self, disc):
    linkname = self.year + LINK_SEPARATOR  
    linkname += self.month + LINK_SEPARATOR  
    linkname += self.day + LINK_SEPARATOR
    linkname += self.filename
    path = join(disc.disc_path, REDUN_DIRNAME, link_name)
    return path

  def get_size(self):
    return os.path.getsize(self.source_path())

"""                                    """
""" Beginning of the modules functions """
"""                                    """

def main():
  print 'Welcome to F-spot backup in Python\n\n'
  print 'Maximum amount of bytes per disc (given ', WANTED_REDUNDANCY, '%):', TO_BE_USED
  setup_stage()
  filter_relevant_dirs()
  disc_no = 1
  disk_usage = 0
  disc = Disc(disc_no)
  disc.setup_disc()
  for day in relevant_days:
    day.scan()
    if (day.size + disc.size) > TO_BE_USED:
      disc_no += 1
      disc = Disc(disc_no)
      disc.setup_disc()
    #link_to_path(target_path, path)
    disc.add(day)
    day.make_dir(disc)
    day.make_links(disc)
  for disc in created_discs:
    print disc
    disc.create_filelist()

def setup_stage():
  """Sets up the stage directory where we are going the create discs from
   the photo directory
   """
  global PHOTOS_DIR_BASENAME 
  PHOTOS_DIR_BASENAME = basename(PHOTOS_DIR)
  if not exists(STAGE):
    mkdir(STAGE)

def tuples_for_day(year, month, day):
  """Make all different ways of spelling the directory
     whether or not zero padding could be added."""
  tuples = []
  year_str = `year`
  month_str = `month`
  day_str = `day`
  tuples.append((year_str, month_str, day_str))
  if month < 10:
    month_str = ('%02d') % month
    tuples.append((year_str, month_str, day_str))
    if day < 10:
      day_str = ('%02d') % day
      tuples.append((year_str, month_str, day_str))
      tuples.append((year_str, `month`, day_str))
  elif day < 10:
    day_str = ('%02d') % day
    tuples.append((year_str, month_str, day_str))
  return tuples

def deal_with_possible_day(year, month, day):
  for day in tuples_for_day(year, month, day):
    if exists(join(PHOTOS_DIR, day[0], day[1], day[2])):
      global relevant_days
      relevant_days.append(Day(day[0], day[1], day[2]))

def filter_relevant_dirs(start=START_DATE, end=END_DATE):
  """ Finds all possible dates from the start to the end. """ 
  start_date = date(start[0], start[1], start[2])
  end_date = date(end[0], end[1], end[2])
  one_day = timedelta(days=1)
  current_date = start_date
  while current_date <= end_date:
    deal_with_possible_day(current_date.year, current_date.month, current_date.day)
    current_date += one_day


if __name__ == "__main__":
      main()
