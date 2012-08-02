#!/usr/bin/env python

from lib import db as db_lib
from lib import geo
from pymongo.helpers import bson
import argparse
import base64
import json
import logging
import os
import time
import tornado.auth
import tornado.ioloop
import tornado.template
import tornado.web
import urllib

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')
parser.add_argument('--port', type=int, default=8888)
args = parser.parse_args()


class Application(tornado.web.Application):
  def __init__(self):
    handlers = [(r'/restos', RestosHandler),
                (r'/edit_resto', EditRestoHandler),
                (r'/auth/login', AuthLoginHandler),
                (r'/auth/logout', AuthLogoutHandler),]
    # Load or generate a secret value for login/auth data.
    if os.path.exists('cookie_secret'):
      cookie_secret = file('cookie_secret').read().strip()
    else:
      logging.warning('File "cookie_secret" not found. Generating one-time'
                      ' value. ')
      cookie_secret = base64.b64encode(os.urandom(64))

    settings = {'debug': args.debug,
                'cookie_secret': cookie_secret,
                'template_path': 'templates',
                'login_url': '/auth/login'}
    tornado.web.Application.__init__(self, handlers, **settings)
    # Global db handler.
    self.db = db_lib.RestoDB()


class BaseHandler(tornado.web.RequestHandler):
  @property
  def db(self):
    return self.application.db

  def get_current_user(self):
    user_id = self.get_secure_cookie('user')
    if not user_id:
      return None
    
    current_user = self.db.resto_users.find_one({'_id': bson.ObjectId(user_id)})
    if not current_user:
      logging.info('User cookie decrypted, but not found in DB. (%s).',
                   current_user)
    return current_user


class RestosHandler(BaseHandler):
  def get(self):
    # 3 ms
    restos_by_arr = {}
    for resto in self.db.paris_restos.find():
      arr = resto.get('postal_code', 'Unknown')
      d = {'name': resto['name'],
           'short_address': resto['address'].split(',')[0],
           'map_link': geo.gen_map_link(resto['address'], resto['name']),
           'edit_link': '/edit_resto?id=%s' % urllib.quote(str(resto['_id']))}
      restos_by_arr.setdefault(arr, []).append(d)

    # 30 ms
    for i in range(75001,75021) + ['Unknown',]:
      if str(i) in restos_by_arr:
        restos_by_arr[str(i)].sort(key=lambda x: x['name'])

    if self.get_argument('format', None) == 'json':
      self.write(json.dumps(restos_by_arr))
    else:
      self.render('restos.tmpl', restos_by_arr=restos_by_arr)
      # 40 ms


class EditRestoHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    resto_id = self.get_argument('id')
    resto = self.db.paris_restos.find_one(bson.ObjectId(resto_id))
    if resto:
      self.render('edit_resto.tmpl', resto=resto)
    else:
      self.send_error(404)

  @tornado.web.authenticated
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
    self.db.paris_restos.update({'_id': resto_id},
                           {'$set': d})
    self.redirect('/restos')


class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
  @tornado.web.asynchronous
  def get(self):
    if self.get_argument("openid.mode", None):
      self.get_authenticated_user(self.async_callback(self._on_auth))
      return
    self.authenticate_redirect()
    
  def _on_auth(self, user):
    if not user:
      raise tornado.web.HTTPError(500, "Google auth failed")

    result = self.db.resto_users.find_one({'email': user['email']})
    if result:
      self.set_secure_cookie('user', str(result['_id']))
      self.redirect(self.get_argument('next', '/'))
    else:
      raise tornado.web.HTTPError(403)


class AuthLogoutHandler(BaseHandler):
  def get(self):
    self.clear_cookie('user')
    self.redirect(self.get_argument('next', '/'))


if __name__ == '__main__':
  if args.debug:
    logging.getLogger().setLevel(logging.INFO)
  else:
    logging.getLogger().setLevel(logging.DEBUG)
  Application().listen(args.port)
  tornado.ioloop.IOLoop.instance().start()
