#!/usr/bin/env python2.7

from lib import db as db_lib
from lib import geo
import argparse
import logging
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--name', required=True,
                    help='Name of the restaurant.')
parser.add_argument('-c', '--coords',
                    help='lat,lon. Will reverse geocode to address.')
parser.add_argument('-d', '--description', default='',
                    help='Description of the restaurant.')
parser.add_argument('-a', '--address',
                    help='Address. Will geocode this into coords.')
parser.add_argument('--debug', action='store_true')
ARGS = parser.parse_args()

def main():
  if ARGS.debug:
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.WARNING)    
  db = db_lib.RestoDB()
  resto = {'name': ARGS.name}
  if db.paris_restos.find_one({'name': ARGS.name}):
    logging.fatal('Restaurant already exists!')
    sys.exit(1)

  resto['description'] = ARGS.description
    
  if ARGS.coords:
    lat, lon = ARGS.coords.split(',')
    geo_query = (lat, lon)
  else:
    if ARGS.address:
      geo_query = ARGS.address
    else:
      logging.fatal('No coords or address given.')
      sys.exit(os.EX_USAGE)

  geo_results = geo.GeoLoc(geo_query)
  if geo_results:
    resto['address'] = geo_results.address
    resto['loc'] = {'lat': float(geo_results.latlng[0]),
                    'lon': float(geo_results.latlng[1])}
    resto['postal_code'] = geo_results.postal_code
  else:
    logging.warning('Unable to geocode "%s" properly.', geo_query)
      
  logging.debug(resto)
  db.paris_restos.insert(resto)


if __name__ == '__main__':
  main()
