#!/usr/bin/env python2.7

from lib import db as db_lib
from lib import geo
from pymongo import Connection
import argparse
import cStringIO
import json
import logging
import os
import pycurl
import sys
import time

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
args = parser.parse_args()

def main():
  if args.debug:
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.WARNING)    
  db = db_lib.RestoDB()
  resto = {'name': args.name}
  if db.paris_restos.find_one({'name': args.name}):
    logging.fatal('Restaurant already exists!')
    sys.exit(1)

  resto['description'] = args.description
    
  if args.coords:
    lat, lon = args.coords.split(',')
    geo_query = (lat, lon)
  else:
    if args.address:
      geo_query = args.address
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
    logging.warning('Unable to geocode "%s" properly.' % geo_query)
      
  logging.debug(resto)
  db.paris_restos.insert(resto)


if __name__ == '__main__':
	main()
