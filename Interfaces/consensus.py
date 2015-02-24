class Default(object):
  def __init__(self):
    self.d = {}
  
  def setValue(self, key, value, interface):
    self.d[key] = value
    nodes = interface.get_endpoints() #get total numver of endpoints
    for ep in range(1, nodes):
      interface.sendMessage(ep, {'key': key, 'value': value})
  
  def getValue(self, key, interface):
    return self.d.get(key)
  
  def gotMessage(self, msg, interface):
    self.d[msg['key']] = msg['value']
