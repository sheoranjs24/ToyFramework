from twisted.internet.protocol import DatagramProtocol
import json

class Framework(DatagramProtocol):

  #algorithm instance
  al = None
  
  #init instance local and master are tuple for listening and connecting
  #  which is in (host_ip, port) format
  def __init__(self, local, master, logfile='log.log'):
    self.master = master
    self.endpoints = [local]
    self.listen_host, self.listen_port = local
    self.logfile = logfile
    self.log = []

  #called by twisted when reactor starts
  def startProtocol(self):
    if self.master and self.master[0] and self.master[1]:
      self.send(self.master, {'type':'init'})
    try:
      log = open(self.logfile, 'r')
      for line in log:
        self.log.append(json.loads(line))
    except:
      pass
    self.al.start(self)


  def send(self, addr, data):
    self.transport.write(json.dumps(data), addr)

  #called by twisted when datagram in comming
  def datagramReceived(self, datagram, addr):
    try:
      data = json.loads(datagram)
    except:
      return

    print data
    if data['type'] == 'init':
      if addr not in self.endpoints:
        self.endpoints.append(addr)
      msg = {'type': 'peer','endpoints': self.endpoints}
      for ep in self.endpoints[1:]:
        self.send(ep, msg);
    elif data['type'] == 'set':
      self.al.setValue(data['key'], data['value'], self)
    elif data['type'] == 'get':
      v = self.al.getValue(data['key'], self)
      msg = {'type': 'answer', 'key': data['key'], 'value': v}
      self.send(addr, msg)
    elif data['type'] == 'peer':
      for ep in data['endpoints']:
        if tuple(ep) not in self.endpoints:
          self.endpoints.append(tuple(ep))
    elif data['type'] == 'msg':
      self.al.gotMessage(data, self)
  
  # append an object to log
  def write_log(self, data):
    try:
      f = open(self.logfile, 'a')
      f.write(json.dumps(data) + '\n')
      f.close()
    except:
      pass
    self.log.append(data)
    

  # get log by index
  def get_log(self, seq):
    if seq >= 0 and seq < len(self.log):
      return self.log[seq]
    else:
      return None
  
  # log are indexed from [0, 1, ..., get_log_count() - 1]
  def get_log_count(self):
    return len(self.log)

  def get_endpoints(self):
    return len(self.endpoints)

  def sendMessage(self, endpoint, data):
    data['type'] = 'msg'
    self.send(self.endpoints[endpoint], data);

  def setAlgorithm(self, al):
    self.al = al
  
  def run(self):
    from twisted.internet import reactor
    reactor.listenUDP(self.listen_port, self, self.listen_host)
    reactor.run()

