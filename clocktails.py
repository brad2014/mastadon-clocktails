#!/usr/bin/python

from mastodon import Mastodon
import os
import time
import re
import string
import random
import urllib
import sys

########################################################################
#
# The file from which we read timezones, cities, and long/lat 
# Exists on CentOS and MacOS at this location. YMMV.
#
zone_tab = '/usr/share/zoneinfo/zone.tab'

########################################################################
#
# get_parameter: Read login parameters from a secrets file
#
def get_parameter( parameter, file_path ):
    # Check if secrets file exists
    if not os.path.isfile(file_path):    
      print("File %s not found, exiting."%file_path)
      sys.exit(0)

    # Find parameter in file
    with open( file_path ) as f:
      for line in f:
        if line.startswith( parameter ):
          return line.replace(parameter + ":", "").strip()

    # Cannot find parameter, exit
    print(file_path + "  Missing parameter %s "%parameter)
    sys.exit(0)

########################################################################
#
# convert2google: Convert zone.tab lat/long to google/maps lat/long
#
# In zone.tab, lat/long is in minutes/seconds, either +-DDMM+-DDDMM or +-DDMMSS+-DDDMMSS
# Google expects decimal numbers.
#
def convert2google( ll ):
  m = re.match(r'^([+-][0-9]{2,3})([0-9]{2})([0-9]{2})?([+-][0-9]{2,3})([0-9]{2})([0-9]{2})?$', ll)
  if not m:
    print "Unable to parse lat/long %s" % ll
    sys.exit(1)
  g = m.groups()
  v1 = float(g[0])
  if g[1]:
    v1 += float(g[1])/60.0
  if g[2]:
    v1 += float(g[2])/3600.0
  v2 = float(g[3])
  if g[4]:
    v2 += float(g[4])/60.0
  if g[5]:
    v2 += float(g[5])/3600.0
  result = "%f,%f" % (v1,v2)
  # print "converted %s to %s\n" % (ll,result)
  return result


########################################################################
#
# Register app and login, but only if we haven't done so already.
# Persistent credentials are shared in the secrets subdirectory.
#
hostname = get_parameter('mastodon_hostname', 'secrets/secrets.txt')
email = get_parameter('app_login_email', 'secrets/secrets.txt')
password = get_parameter('app_login_password', 'secrets/secrets.txt')

if not os.path.isfile('secrets/clientcred.txt'):
  print "Creating app clocktails..."
  Mastodon.create_app(
    'clocktails',
    to_file = 'secrets/clientcred.txt',
    api_base_url='https://'+hostname
  )

if not os.path.isfile('secrets/usercred.txt'):
  print "Logging in..."
  mastodon = Mastodon(
    client_id = 'secrets/clientcred.txt',
    api_base_url='https://'+hostname
  )
  mastodon.log_in( email, password, to_file = 'secrets/usercred.txt' )

########################################################################
#
# Look up cities on selected continents, and find the time in each one.
#
if not os.path.isfile(zone_tab):
  print("File %s not found, exiting." % zone_tab)
  sys.exit(0)

now = time.time()
waitmap = {}
longlat = {}
with open( zone_tab ) as f:
  for line in f:
    zone = None
    l = line.split("\t")
    if len(l) != 4:
      continue

    (country,ll,zone,label) = l
    if not zone:
      continue

    if zone.startswith('Antarctica'):
      continue

    os.environ['TZ'] = zone
    time.tzset()
    (x,x,x,hour,min,sec,x,x,x) = time.localtime(now)

    # How many seconds until the next 5pm?
    # (yeah, sometimes wrong for cities starting/ending DST tomorrow, but doesn't matter)
    wait = ((24+17)*3600 - (((hour*60)+min)*60+sec)) % (24*3600)

    # Group the zones by wait time, and save the long/lat
    if not wait in waitmap:
      waitmap[wait] = []
    waitmap[wait].append(zone)
    longlat[zone] = ll

# Pick a random city in the next upcoming cocktail hour
min_wait = sorted(waitmap.keys())[0]
random_zone = random.choice( waitmap[min_wait] )

(region,city) = random_zone.split('/')
city = string.replace(city, '_', ' ')


# Build a maps query to local bars
#
url = "https://www.google.com/maps/search/%s/@%s,9z/" % (urllib.quote('bars near %s' % city),convert2google(longlat[random_zone]))

toot = "It is 5 p.m. in %s!\nTime for a cocktail!\n%s" % (city, url)

limit = 30 # minutes
if min_wait > limit*60:
  print "No cocktails in the next %s minutes.  Try again later." % limit
  sys.exit(0)

print "Waiting %d'%d\" to post:\n%s" % (min_wait/60, min_wait%60, toot)
time.sleep(min_wait)
mastodon = Mastodon(
  client_id = 'secrets/clientcred.txt',
  access_token = 'secrets/usercred.txt',
  api_base_url='https://'+hostname
  )
mastodon.toot(toot)
