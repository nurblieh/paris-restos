#!/usr/bin/env python2.7

from pymongo import Connection
import xml.etree.ElementTree as ET
import time

def build_resto_list():
  restos = []
  myParis = ET.parse('My Paris.kml')
  root = myParis.getroot()
  ns = root.tag.replace('}kml', '}')
  doc = root.getchildren()[0]
  for place in doc.findall('%sPlacemark' % ns):
    info = {'date': time.time()}
    for child in place.getchildren():
      name = child.tag.split('}')[1]
      if name == 'Point':
        lon, lat, elev = child.getchildren()[0].text.split(',')
        info['coordinates'] = {'lat': lat, 'lon': lon}
      elif name in ('description', 'name'):
        info[name] = child.text
    restos.append(info)

  return restos

def main():
  resto_list = build_resto_list()

  m_conn = Connection('localhost:27017')
  # DBs and collections are lazily and automatically created.
  m_db = m_conn.db1
  m_paris_restos = m_db.paris_restos

  # bulk insert by passing interator.
  m_paris_restos.insert(resto_list)

  print "# of restos inserted: %d" % m_paris_restos.count()

if __name__ == '__main__':
  main()
