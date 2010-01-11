#!/usr/bin/env python

""" This script should take care of creating multi dvds from your f-spot
    Photos map. With the following features:
    The photos are directely visible from disc.
    Redundency is added, to ensure recovery when the disc gets damaged.
    The photo database is added to every disc.
    Staging for creation of a disc is done by hardlinking when possible.
    You can specify where to start and where to end.
    """

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
SUPER_SCRIPT = 'fsbackup_batch.sh'
FILELIST_POSTFIX = '_file.list'
REPAIR_SCRIPT = 'par2repair.sh'
CREATE_PAR2_SCRIPT = 'par2create.sh'
VERIFY_SCRIPT = 'par2verify.sh'
CREATE_LINKS_SCRIPT = 'create_links.sh'
REMOVE_LINKS_SCRIPT = 'remove_links.sh'
CREATE_ISO_SCRIPT = 'create_iso_image.sh'
SCRIPTS = [REPAIR_SCRIPT, CREATE_LINKS_SCRIPT, REMOVE_LINKS_SCRIPT, VERIFY_SCRIPT, CREATE_PAR2_SCRIPT, CREATE_ISO_SCRIPT]
SCRIPTS_DIR = 'scripts'
PHOTOS_DB=expanduser('~/.gnome2/f-spot/photos.db')
REDUNDANCY=WANTED_REDUNDANCY+8
DISK=4700000000
TO_BE_USED=DISK*100/(100+REDUNDANCY)
LINK_SEPARATOR='___'

relevant_days = []

def create_super_script():
  script_path = join(STAGE, SUPER_SCRIPT)
  super_script = open(script_path, 'w')
  content = ''
  for disc in Disc.created_discs:
    content += 'cd ' + join(disc.name, SCRIPTS_DIR) + '\n'
    content += './' + CREATE_PAR2_SCRIPT + '\n'
    content += './' + CREATE_ISO_SCRIPT + '\n'
    content += 'cd ../..\n\n'
  super_script.write(content)
  super_script.close()
  os.chmod(script_path, 0755)

class Disc(object):
  """ One medium volume """
  created_discs = []
  


  def __init__(self, disc_no):
      self.disc_no = disc_no
      self.days = []
      self.size = 0

  def create_scripts(self):
    self.create_par2create_script()
    self.create_par2verify_script()
    self.create_par2repair_script()
    self.create_link_removal_script()
    self.create_link_creation_script()
    self.create_iso_script()
    self.create_filelist()

  def setup_disc(self):
    """ Sets the stage for one particular disc in this backup
        set. 
        """
    disc_no_str = ('%03d') % (self.disc_no + (FIRST_DISC_NO - 1))
    self.name = DISC_PREFIX + disc_no_str
    self.path = join(STAGE, self.name)
    self.target_path = join(self.path, PHOTOS_DIR_BASENAME)
    self.redundancy_path = join(self.path, REDUN_DIRNAME)
    self.script_dir = join(self.path, SCRIPTS_DIR)
    os.makedirs(self.target_path)
    mkdir(self.redundancy_path)
    mkdir(self.script_dir)
    Disc.created_discs.append(self)
    self.copy_photos_db()
    self.copy_software()

  def add(self, day):
    self.days.append(day)
    self.size += day.size

  def copy_software(self):
    software_path = dirname(__file__)
    software_target = join(self.path, SOFTWARE_DIR)
    shutil.copytree(software_path, software_target)

  def copy_photos_db(self):
    shutil.copy(PHOTOS_DB, self.path)

  def create_par2create_script(self):
    content = './' + CREATE_LINKS_SCRIPT + '\n'
    content += 'cd ../' + REDUN_DIRNAME + '\n'
    content += 'par2 c -b3200 -r' + `WANTED_REDUNDANCY` + ' ' + self.name + ' *'  
    self.write_script(CREATE_PAR2_SCRIPT, content)
  
  def create_par2verify_script(self):
    content = './' + CREATE_LINKS_SCRIPT + '\n'
    content += 'cd ../' + REDUN_DIRNAME + ' && ' 
    content += 'par2 v ' + self.name + '.par2\n'  
    self.write_script(VERIFY_SCRIPT, content)

  def create_iso_script(self):
    content = './' + REMOVE_LINKS_SCRIPT + '\n'
    content += 'cd ../\n'
    content += 'genisoimage -V ' + self.name + ' -R -J -iso-level 4 -o ../' + self.name + '.iso *\n'
    self.write_script(CREATE_ISO_SCRIPT, content)

  def create_par2repair_script(self):
    content = 'cd ../' + REDUN_DIRNAME + '\n'
    content += 'par2 r ' + self.name + '.par2\n'  
    self.write_script(REPAIR_SCRIPT, content)


  def create_link_creation_script(self):
    def link(source, target):
      return 'ln "' + source + '" "' + target + '"\n'

    content = 'cd ..\n'
    for script in SCRIPTS:
      content += link(join(SCRIPTS_DIR, script), join(REDUN_DIRNAME, script))
    photo_db_basename = basename(PHOTOS_DB)
    content += link(photo_db_basename, join(REDUN_DIRNAME, photo_db_basename))
    for day in self.days:
      for file in day.files:
        content += link(file.ondisc_path(self), file.redundancy_path(self))
    self.write_script(CREATE_LINKS_SCRIPT, content)
    

  def create_link_removal_script(self):
    def rm(target):
      return 'rm "' + target + '"\n'

    content = 'cd ../' + REDUN_DIRNAME + '\n'
    content += rm(basename(PHOTOS_DB))
    for script in SCRIPTS:
      content +=  rm(script)
    content += 'cd ..\n'
    for day in self.days:
      for file in day.files:
        content += rm(file.redundancy_path(self))
    self.write_script(REMOVE_LINKS_SCRIPT, content)

  def write_script(self, script_name, content):
    script_path = join(self.script_dir, script_name)
    script = open(script_path, 'w')
    script.write(content)
    script.close()
    os.chmod(script_path, 0755)

  def create_filelist(self):
    file_list = open(join(self.path, self.name + FILELIST_POSTFIX), 'w')
    for day in self.days:
      for file in day.files:
        file_list.write(file.ondisc_path(self) + ' (' + file.source_path() + ')\n')
    file_list.close()


class Day(object):
  """ Respresents one lowest level directory to be backed up """
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
    path = join(disc.target_path,
    self.year, 
    self.month, 
    self.day)
    return path
  
  def make_dir(self, disc):
    os.makedirs(join(disc.target_path, self.year, self.month, self.day))

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
    path = join(REDUN_DIRNAME, linkname)
    return path

  def get_size(self):
    return os.path.getsize(self.source_path())

"""                                    """
""" Beginning of the modules functions """
"""                                    """

def main():
  print 'Welcome to F-spot backup in Python\n'
  print 'Maximum amount of bytes per disc (given ', WANTED_REDUNDANCY, '%):', TO_BE_USED , '\n'
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
    disc.add(day)
    day.make_dir(disc)
    day.make_links(disc)
  for disc in Disc.created_discs:
    print 'Creating scripts for ' + disc.name + '. Diskspace used: ' + str(disc.size)
    disc.create_scripts() 
  create_super_script()
  print '\nDone (you can type "cd ' + STAGE + ' && ./' + SUPER_SCRIPT + '").'

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
