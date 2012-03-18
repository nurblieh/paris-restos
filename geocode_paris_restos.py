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
  m_paris_restos = get_resto_collection()

  for resto in m_paris_restos.find():
    lat, lon = resto.coordinates['lat'], resto.coordinates['lon']
    