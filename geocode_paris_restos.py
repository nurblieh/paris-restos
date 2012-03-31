#!/usr/bin/env python2.7

# Google Maps API reference on reverse geocoding.
# https://developers.google.com/maps/documentation/geocoding/#ReverseGeocoding


from pymongo import Connection
import time

def get_resto_collection():
  m_conn = Connection('localhost:27017')
  # DBs and collections are lazily and automatically created.
  m_db = m_conn.db1
  return m_db.paris_restos


def main():
  coll_paris_restos = get_resto_collection()
  for resto in coll_paris_restos.find():
    if 'address' not in resto:
      resto_id = resto._id
      lat, lon = resto.coordinates['lat'], resto.coordinates['lon']
      # TODO: do reverse geocode.
      # example url: http://maps.googleapis.com/maps/geo?q=40.714224,-73.961452&output=json&sensor=true_or_false&key=your_api_key
      url = 'http://maps.googleapis.com/maps/geo?'
      url += 'q=%s,%s' % (lat, lon)
      url += '&output=json&sensor=false'
      # addr_str = geocode.get(url)
      print ''%s: %s'' % (resto.name, addr_str)
      coll_paris_restos.update({'_id': resto_id},
                               {'$set': {'address': addr_str},
                               safe=True)


