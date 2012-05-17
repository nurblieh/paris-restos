#!/usr/bin/env python2.7

import cStringIO
import json
import logging
import pycurl
import urllib

# Google Maps API reference on reverse geocoding.
# https://developers.google.com/maps/documentation/geocoding/#ReverseGeocoding
MAP_API_URL_BASE = ('http://maps.googleapis.com/maps/api/geocode/json?'
                    'sensor=false&')

def _query_maps_api(url):
  buf = cStringIO.StringIO()
  c = pycurl.Curl()
  c.setopt(c.URL, str(url))
  c.setopt(c.WRITEFUNCTION, buf.write)
  c.setopt(c.TIMEOUT, 10)
  c.perform()
  d = json.loads(buf.getvalue())
  buf.close()
  return d

class GeoLoc(object):
  """docstring for GeoLoc"""
  def __init__(self, arg=None):
    self.address = ''
    self.latlng = {}
    self.postal_code = None

    if arg:
      if isinstance(arg, str):
        self.geocode_address(arg)
      elif isinstance(arg, (list, tuple)):
        self.geocode_latlng(arg)
      else:
        logging.error('Unknown arg to GeoLoc constructor.')

  def geocode_address(self, address):
    params = {'address': address}
    self._geocode(params)

  def geocode_latlng(self, latlng):
    params = {'latlng': ','.join(latlng[0:2])}
    self._geocode(params)

  def _geocode(self, params):
    self.address = ''
    self.latlng = {}
    self.postal_code = None
    url = MAP_API_URL_BASE + urllib.urlencode(params)
    logging.debug('maps query url: %s' % url)
    maps_data = _query_maps_api(url)
    if maps_data['status'] == 'OK':
      maps_data = maps_data['results'][0]
      self.latlng = (maps_data['geometry']['location']['lat'],
                     maps_data['geometry']['location']['lng'])
      self.address = maps_data['formatted_address']
      for i in maps_data['address_components']:
        if 'postal_code' in i['types']:
          self.postal_code = i['short_name']
          break
    else:
      logging.error('maps query failed.')
      logging.error('maps api result: %s' % maps_data['status'])

