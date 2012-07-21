#!/usr/bin/env python

from lib import db as db_lib
from lib import geo
from pymongo import Connection
from pymongo.helpers import bson
import argparse
import json
import logging
import os
import pprint
import time
import tornado.ioloop
import tornado.template
import tornado.web
import urllib

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--port', type=int, default=8888)
args = parser.parse_args()

class RestosHandler(tornado.web.RequestHandler):
  def get(self):
    t = time.time()
    # 3 ms
    restos_by_arr = {}
    for resto in db.paris_restos.find():
      d = {'name': resto['name'],
           'short_address': resto['address'].split(',')[0],
           'map_link': geo.gen_map_link(resto['address'], resto['name']),
           'edit_link': '/edit_resto?id=%s' % urllib.quote(str(resto['_id']))}
      restos_by_arr.setdefault(int(resto['postal_code']), []).append(d)

      # 30 ms
    if self.get_argument('format', None) == 'json':
      self.write(json.dumps(restos_by_arr))
    else:
      self.write(template_loader.load('restos.tmpl').generate(restos_by_arr=restos_by_arr))
      # 40 ms

class EditRestoHandler(tornado.web.RequestHandler):
  def get(self):
    # template rendering is slow!
    resto_id = self.get_argument('id')
    resto = db.paris_restos.find_one(bson.ObjectId(resto_id))
    if resto:
      self.write(template_loader.load('edit_resto.tmpl').generate(resto=resto))
    else:
      self.send_error(404)


  def post(self):
    # TODO: form validation.
    d = {}
    resto_id = bson.ObjectId(self.get_argument('_id'))
    d['name'] = self.get_argument('name')
    d['address'] = self.get_argument('address')
    d['loc'] = {'lat': float(self.get_argument('lat')),
                'lon': float(self.get_argument('lon'))}
    d['description'] = self.get_argument('description', "")
    d['postal_code'] = self.get_argument('postal_code')
    # TODO: create backup table.
    db.paris_restos.update({'_id': resto_id},
                           {'$set': d})
    self.redirect('/restos')


if __name__ == '__main__':
  if args.debug:
    logging.getLogger().setLevel(logging.INFO)
  else:
    logging.getLogger().setLevel(logging.DEBUG)
  template_loader = tornado.template.Loader('templates')
  application = tornado.web.Application([
    (r"/restos", RestosHandler),
    (r"/edit_resto", EditRestoHandler),
  ])
  application.listen(args.port)
  global db
  db = db_lib.RestoDB()
  tornado.ioloop.IOLoop.instance().start()
