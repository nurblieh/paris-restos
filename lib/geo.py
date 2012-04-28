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

def geocode(query):
  url = MAP_API_URL_BASE
  if isinstance(query, str):
    # We received a string containing an address.
    params = {'address': query}
    url += urllib.urlencode(params)
  elif isinstance(query, (list, tuple)):
    # We received a tuple of lat,lon.
    if len(query) == 2:
      params = {'latlng': ','.join(query[0:2])}
      url += urllib.urlencode(params)

  if url == MAP_API_URL_BASE:
    logging.error('We didn\'t receive properly a formatted' 
                  'address or latlng.')
    return None

  logging.debug('maps query url: %s' % url)
  maps_data = _query_maps_api(url)
  results = {}
  if maps_data['status'] == 'OK':
    maps_data = maps_data['results'][0]
    # This is a dict {'lat': float, 'lng': float}
    results['latlng'] = {'lat': maps_data['geometry']['location']['lat'],
                         'lon': maps_data['geometry']['location']['lng']}
    results['address'] = maps_data['formatted_address']
    for i in maps_data['address_components']:
      if 'postal_code' in i['types']:
        results['postal_code'] = i['short_name']

  else:
    logging.error('maps query failed.')
    logging.error('maps api result: %s' % maps_data['status'])

  return results