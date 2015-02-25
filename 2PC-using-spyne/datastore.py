import json
import os
import logging
import pickle

import transaction

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(level)s: %(message)s')
#logging.getLogger(__name__).setLevel(logging.INFO)

class DataStore(object):
    
    def __init__(self, name='datastore', file_path='datastore.pkl'):
        self.name = name
        self.data_path = file_path
        self.uncommitted = {}
        self.commited = {}
        
        # Read the datastore file and load data
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
            print 'key not found'
            return None
        return value
    
    def put_value(self, key, value):
        self.uncommitted[key] = value
    
    def delete_key(self, key):
        try:
            self.uncommitted.pop(key)
        except KeyError:
            print 'key not found'
    
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