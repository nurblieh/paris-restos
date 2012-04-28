#!/usr/bin/env python2.7

from pymongo import Connection

LOCAL_DB = 'localhost:27017'

class RestoDB(object):
  def __init__(self):
    conn = Connection(LOCAL_DB, safe=True, fsync=True)
    db = conn.db1
    self.paris_restos = db.paris_restos

  # def add_resto(self, name, **kwargs):
  #   fields = (name, description, address, coordinates)
  #   resto = {'name': name}
  #   for k, v in kwargs.iteritems():
  #     if k == 'coordinates':

  #     if k in fields:


