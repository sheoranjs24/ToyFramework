from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import stdio
from twisted.protocols import basic

import optparse, json


def parse_args():
  usage = """usage: %prog [hostname:]port

This is the framework client, run like this:

  python client.py [option] <host ip and port to connect>
"""
  
  parser = optparse.OptionParser(usage)
  
  option, arg = parser.parse_args()
 
  if len(arg):
    if ':' not in arg[0]:
      option.port = arg[0]
      option.host = '127.0.0.1'
    else:
      option.host, option.port = arg[0].split(':', 1)
    option.port = int(option.port)
  else:
    parser.error("Need server [ip:]port")

  return option

class Udp(DatagramProtocol):
 
  def __init__(self, host, port):
    self.host = host
    self.port = port
  
  def startProtocol(self):
    self.transport.connect(self.host, self.port)
  
  def datagramReceived(self, datagram, addr):
    data = json.loads(datagram)
    print data['key'], '=', data['value']
  
  def send(self, data):
    self.transport.write(json.dumps(data))
    

class Console(basic.LineReceiver):
  from os import linesep as delimiter
  def __init__(self, udp):
    self.udp = udp
  
  def connectionMade(self):
    pass
  
  def lineReceived(self, line):
    cmd = line.split(' ', 2)
    data = {'type': None}
    if cmd[0] == 'get' and len(cmd) == 2:
      data['type'] = 'get'
      data['key'] = cmd[1]
    if cmd[0] == 'set' and len(cmd) == 3:
      data['type'] = 'set'
      data['key'] = cmd[1]
      data['value'] = cmd[2]
    if data['type']:
      self.udp.send(data)
    if cmd[0] == 'exit':
      from twisted.internet import reactor
      reactor.stop()
      

def main():
  import consensus
  opt = parse_args()
  udp = Udp(opt.host, opt.port)
  
  from twisted.internet import reactor
  stdio.StandardIO(Console(udp))
  reactor.listenUDP(0, udp)
  reactor.run()

if __name__ == "__main__":
  main()

