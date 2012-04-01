#!/usr/bin/env python2.7

# Google Maps API reference on reverse geocoding.
# https://developers.google.com/maps/documentation/geocoding/#ReverseGeocoding

from pymongo import Connection
import cStringIO
import json
import pycurl
import time

def get_resto_collection():
  m_conn = Connection('localhost:27017')
  # DBs and collections are lazily and automatically created.
  m_db = m_conn.db1
  return m_db.paris_restos

def query_maps_api(url):
  buf = cStringIO.StringIO()
  c = pycurl.Curl()
  c.setopt(c.URL, str(url))
  c.setopt(c.WRITEFUNCTION, buf.write)
  c.setopt(c.TIMEOUT, 10)
  c.perform()
  d = json.loads(buf.getvalue())
  buf.close()
  return d

def main():
  maps_api_url = ('http://maps.googleapis.com/maps/api/geocode/json?'
                  'latlng=%s,%s&sensor=false')
  paris_restos = get_resto_collection()
  for resto in paris_restos.find():
    resto_id = resto['_id']
    lat = resto['coordinates']['lat'] 
    lon = resto['coordinates']['lon']
    d = query_maps_api(maps_api_url % (lat, lon))
    if d['status'] == 'OK':
      # Take the first address.
      d = d['results'][0]
      street_addr = d['formatted_address']
      for i in d['address_components']:
        if 'postal_code' in i['types']:
          postal_code = i['short_name']
          
      print '%s: %s' % (resto['name'], street_addr)
      paris_restos.update({'_id': resto_id},
                          {'$set': {'address': street_addr,
                                    'postal_code': postal_code}},
                          safe=True)
    time.sleep(5)

  return

if __name__ == '__main__':
  main()