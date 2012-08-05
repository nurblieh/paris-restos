#!/usr/bin/env python2.7

from lib import db as db_lib
from lib import geo
from pymongo.helpers import bson
import argparse
import logging
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')

subparsers = parser.add_subparsers()
# Flags for the 'add' command.
parser_add = subparsers.add_parser('add')
parser_add.add_argument('-n', '--name', dest='add_name', required=True,
                        help='Name of the restaurant.')
parser_add.add_argument('-c', '--coords',
                        help='lat,lon. Will reverse geocode to address.')
parser_add.add_argument('-d', '--description', default='',
                        help='Description of the restaurant.')
parser_add.add_argument('-a', '--address',
                        help='Address. Will geocode this into coords.')

# Flags for the 'rm' command.
parser_rm = subparsers.add_parser('rm')
parser_rm.add_argument('rm_id_or_name',
                       help='Name or DB id of the restaurant to delete.')

ARGS = parser.parse_args()


def add_resto():
  resto = {'name': ARGS.add_name}
  if DB.paris_restos.find_one({'name': ARGS.add_name}):
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
      
  logging.info('Inserting resto doc (%s)', str(resto))
  DB.paris_restos.insert(resto)


def rm_resto(name_or_id):
  resto = DB.paris_restos.find_one({'_id': bson.ObjectId(name_or_id)})
  if not resto:
    resto = DB.paris_restos.find_one({'name': name_or_id})

  if not resto:
    logging.fatal('Unable to find restaurant (%s)', name_or_id)
    sys.exit(1)

  logging.info('Removing resto (%s).', str(resto))
  DB.paris_restos.remove(resto)


def main():
  if ARGS.debug:
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO)

  if 'rm_id_or_name' in ARGS:
    rm_resto(ARGS.rm_id_or_name)
  elif 'add_name' in ARGS:
    add_resto()


if __name__ == '__main__':
  DB = db_lib.RestoDB()
  main()
