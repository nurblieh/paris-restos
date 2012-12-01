#!/usr/bin/env python

from lib import db as db_lib
from lib import geo
from pymongo.helpers import bson
import argparse
import base64
import json
import logging
import os
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
                (r'/add_resto', AddRestoHandler),
                (r'/edit_resto', EditRestoHandler),
                (r'/rm_resto', RemoveRestoHandler),
                (r'/auth/login', AuthLoginHandler),
                (r'/auth/logout', AuthLogoutHandler),
                ]
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
                'login_url': '/auth/login',
                'static_path': 'static',
                }
    tornado.web.Application.__init__(self, handlers, **settings)
    # Global db handler.
    self.db = db_lib.RestoDB()


class BaseHandler(tornado.web.RequestHandler):
  @property
  def db(self):
    return self.application.db

  def prepare(self):
    if 'Android' in self.request.headers.get('User-Agent', ''):
      self.mobile_browser = True
    else:
      self.mobile_browser = False

  def get_current_user(self):
    user_id = self.get_secure_cookie('user')
    if not user_id:
      return None

    current_user = self.db.resto_users.find_one(
        {'_id': bson.ObjectId(user_id)})
    if not current_user:
      logging.info('User cookie decrypted, but not found in DB. (%s).',
                   current_user)
    return current_user

  @staticmethod
  def urlescape(string):
    return urllib.quote_plus(string.encode('utf-8'))

class RestosHandler(BaseHandler):
  def get(self):
    # 3 ms
    filter_tag = self.get_argument('tag', None)
    tag_list = set()
    restos_by_zip = {}
    for resto in self.db.paris_restos.find():
      if filter_tag and filter_tag not in resto.get('tags', []):
        continue
      postal_code = resto.get('postal_code', 'Unknown')
      if not postal_code or '75' not in postal_code:
        postal_code = 'Unknown'
      resto_address = resto.get('address', '')
      # keep a list of all known tags, in order to generate links.
      tag_list.update(resto.get('tags', []))
      d = {'name': resto['name'],
           'short_address': resto_address.split(',')[0],
           'tags': resto.get('tags', []),
           'map_link': geo.gen_map_link(resto_address, resto['name']),
           'search_link': ('http://www.google.com/search?q='
                           '%s+Paris+France' % self.urlescape(resto['name'])),
           'edit_link': '/edit_resto?id=%s' % self.urlescape(str(resto['_id'])),
           'rm_link': '/rm_resto?id=%s' % self.urlescape(str(resto['_id'])),
           }
      restos_by_zip.setdefault(postal_code, []).append(d)

    # Sort the restaurants by name.
    for i in range(75001, 75021) + ['Unknown']:
      if str(i) in restos_by_zip:
        restos_by_zip[str(i)].sort(key=lambda x: x['name'])


    if self.get_argument('format', None) == 'json':
      self.write(json.dumps(restos_by_zip))
    else:
      context = {'restos_by_zip': restos_by_zip,
                 'user_authd': True if self.get_current_user() else False,
                 'mobile_browser': self.mobile_browser,
                 'tag_list': tag_list,
                 }
      self.render('restos.tmpl', context=context)

      
class AddRestoHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    self.render('add_resto.tmpl')

  def post(self):
    resto = {}
    resto['name'] = self.get_argument('name')
    if self.db.paris_restos.find_one({'name': resto['name']}):
      self.write('Resto (%s) already exists!' % resto['name'])
      return

    resto['description'] = self.get_argument('description', '')

    if self.get_argument('address', None):
      geo_results = geo.GeoLoc(self.get_argument('address'))
      if geo_results:
        resto['address'] = geo_results.address
        resto['loc'] = {'lat': float(geo_results.latlng[0]),
                        'lon': float(geo_results.latlng[1])}
        resto['postal_code'] = geo_results.postal_code

    self.db.paris_restos.insert(resto)
    self.redirect('/restos')


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
    old_data = self.db.paris_restos.find_one(bson.ObjectId(resto_id))
    if not old_data:
      logging.error('Resto not found. (%s)', resto_id)

    d['name'] = self.get_argument('name')
    d['address'] = self.get_argument('address', '')
    d['postal_code'] = self.get_argument('postal_code', 'Unknown')
    if self.get_argument('lat', None):
      d['loc'] = {'lat': float(self.get_argument('lat')),
                  'lon': float(self.get_argument('lon'))}
    elif d['address']:
      geo_results = geo.GeoLoc(d['address'])
      if geo_results:
        d['address'] = geo_results.address
        d['loc'] = {'lat': float(geo_results.latlng[0]),
                    'lon': float(geo_results.latlng[1])}
        d['postal_code'] = geo_results.postal_code

    d['description'] = self.get_argument('description', '')
    d['tags'] = self.get_argument('tags', '').split(',')
    # TODO: create backup table.
    self.db.paris_restos.update({'_id': resto_id},
                                {'$set': d})
    self.redirect('/restos')


class RemoveRestoHandler(BaseHandler):
  def get(self):
    self.post()

  @tornado.web.authenticated
  def post(self):
    resto_id = bson.ObjectId(self.get_argument('id'))
    resto = self.db.paris_restos.find_one(bson.ObjectId(resto_id))
    if resto:
      try:
        self.db.paris_restos.remove({'_id': resto_id}, safe=True)
      except pymongo.errors.OperationFailure:
        logging.exception('failed to remove doc (%s)', resto_id)
        raise tornado.web.HTTPError(500)
      self.redirect('/restos')
    else:
      self.write('Resto (%s) not found.' % resto_id)


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
      self.redirect(self.get_argument('next', '/restos'))
    else:
      raise tornado.web.HTTPError(403)


class AuthLogoutHandler(BaseHandler):
  def get(self):
    self.clear_cookie('user')
    self.redirect(self.get_argument('next', '/restos'))


if __name__ == '__main__':
  if args.debug:
    logging.getLogger().setLevel(logging.INFO)
  else:
    logging.getLogger().setLevel(logging.DEBUG)
  Application().listen(args.port)
  tornado.ioloop.IOLoop.instance().start()
