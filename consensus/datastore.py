import json, os, logging, pickle

class Database(object):
    
  def __init__(self, name='database', file_path='database.pkl'):
    self.name = name
    self.data_path = file_path
    self.uncommitted = {}
    self.commited = {}
    
    # Read the database file and load data
    try:
      data_file = open(self.data_path, 'r')
    except IOError:
      data_file = None
    uncommitted = {}
    if data_file is not None:
      try:
        uncommitted = pickle.load(data_file)
      except EOFError:
          pass
    self.uncommitted = uncommitted
    self.committed = uncommitted.copy()

  def get_value(self, key):
    try:
      value = self.committed[key]
    except KeyError:
      print('key not found')
      return None
    return value
  
  def put_value(self, key, value):
    self.uncommitted[key] = value
  
  def delete_key(self, key):
    try:
      self.uncommitted.pop(key)
    except KeyError:
      print('key not found')

  def get_keys(self):
    return self.uncommitted.keys()

  def get_values(self):
    return self.uncommitted.values()

  def get_items(self):
    return self.uncommitted.items()
  
  def __repr__(self):
    return self.uncommitted.__repr__()
  
  def abort(self):
    self.uncommitted = self.committed.copy()

  def commit(self):
    data_file = open(self.data_path, 'w')
    pickle.dump(self.uncommitted, data_file)
    self.committed = self.uncommitted.copy()
