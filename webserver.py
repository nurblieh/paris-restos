#!/usr/bin/env python

from lib import db as db_lib
from pymongo import Connection
import argparse
import os
import pprint
import tornado.ioloop
import tornado.template
import tornado.web

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--port', type=int, default=8888)
args = parser.parse_args()

class RestosHandler(tornado.web.RequestHandler):
  def get(self):
    db = db_lib.RestoDB()
    restos_by_arr = {}
    for postal_code in range(75001, 75021):
      restos_by_arr[postal_code] = []
      #self.write('<b>%s</b></br>\n' % postal_code)
      restos = db.paris_restos.find({'postal_code': str(postal_code)})
      #self.write('<table>')
      for resto in restos:
        short_address = resto['address'].split(',')[0]
        restos_by_arr[postal_code].append({'name': resto['name'],
                                           'short_address': short_address})
        #self.write('<tr><td>%s</td><td>%s</td></tr>' % (resto['name'], short_address))
      #self.write('</table></br>\n')

    pprint.pprint(restos_by_arr)
    template_loader.load('restos.tmpl').generate(restos_by_arr=restos_by_arr)


if __name__ == '__main__':
  my_path = os.path.abspath(__file__)
  template_loader = tornado.template.Loader('templates')
  application = tornado.web.Application([
    (r"/restos", RestosHandler),
  ])
  application.listen(args.port)
  tornado.ioloop.IOLoop.instance().start()
  
