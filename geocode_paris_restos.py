#!/usr/bin/env python2.7

from lib import db as db_lib
from lib import geo
import argparse
import logging
import time

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
args = parser.parse_args()

def main():
  if args.debug:
    logging.basicConfig(level=logging.DEBUG)
  else:
    logging.basicConfig(level=logging.WARNING)

  db = db_lib.RestoDB()
  for resto in db.paris_restos.find():
    resto_id = resto['_id']
    if 'coordinates' not in resto:
      logging.warning('No coordinates for "%s"' % resto['name'])
      continue
    latlng = (resto['coordinates']['lat'],
              resto['coordinates']['lon'])
    resto_loc = geo.GeoLoc(latlng)
    if resto_loc.address:
      logging.debug('%s: %s' % (resto['name'], resto_loc.__dict__))
      # Rename one of the fields from previous attempts.
      db.paris_restos.update({'_id': resto_id},
                             {'$rename': {'coordinates': 'loc'}},
                             safe=True)
      updated_fields = {'address': resto_loc.address,
                        'postal_code': resto_loc.postal_code,
                        'loc': {'lat': float(latlng[0]),
                                'lon': float(latlng[1])}}
      db.paris_restos.update({'_id': resto_id},
                             {'$set': updated_fields},
                             safe=True)

    else:
      logging.error('Failed to geocode %s' % resto['name'])
      
    time.sleep(5)    
    
  return


if __name__ == '__main__':
  main()