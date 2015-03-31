class Default(object):
  def __init__(self):
    self.d = {}
  
  def start(self, interface):
    for i in range(0, interface.get_log_count()):
      self.d[interface.get_log(i)['key']] = interface.get_log(i)['value']

  def setValue(self, key, value, interface):
    interface.write_log({'key':key, 'value':value})
    self.d[key] = value
    nodes = interface.get_endpoints() #get total number of endpoints
    for ep in range(1, nodes):
      interface.sendMessage(ep, {'key': key, 'value': value})
  
  def getValue(self, key, interface):
    return self.d.get(key)
  
  def gotMessage(self, msg, interface):
    self.d[msg['key']] = msg['value']
