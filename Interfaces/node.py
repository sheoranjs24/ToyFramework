from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

import optparse, json


def parse_args():
  usage = """usage: %prog [options] [hostname:]port

This is the framework node, run like this:

  python node.py [option] <host ip and port to listen>
"""
  
  parser = optparse.OptionParser(usage)
  
  help = "The address and port to connect to, in [ip:]port format"
  parser.add_option('--connect', type='string', help=help, default=0)
  
  option, arg = parser.parse_args()
  option.master_host = None
  option.master_port = None
  if option.connect:
    if ':' not in option.connect:
      option.master_host = '127.0.0.1'
      option.master_port = option.connect
    else:
      option.master_host, option.master_port = option.connect.split(':', 1)
    option.master_port = int(option.master_port)
  
  if len(arg):
    if ':' not in arg[0]:
      option.port = arg[0]
      option.host = '127.0.0.1'
    else:
      option.host, option.port = arg[0].split(':', 1)
    option.port = int(option.port)
  else:
    parser.error("Need listening [ip:]port")

  return option

class Framework(DatagramProtocol):
 
  al = None 
  def __init__(self, local, master):
    self.master = master
    self.endpoints = [local]

  def startProtocol(self):
    if self.master and self.master[0] and self.master[1]:
      self.send(self.master, {'type':'init'})
  
  def send(self, addr, data):
    self.transport.write(json.dumps(data), addr)
  
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

  def get_endpoints(self):
    return len(self.endpoints)

  def sendMessage(self, endpoint, data):
    data['type'] = 'msg'
    self.send(self.endpoints[endpoint], data);

def main():
  import consensus
  opt = parse_args()
  protocol = Framework((opt.host, opt.port), (opt.master_host, opt.master_port))
  protocol.al = consensus.Default();
  
  from twisted.internet import reactor
  reactor.listenUDP(opt.port, protocol, opt.host)
  reactor.run()

if __name__ == "__main__":
  main()

