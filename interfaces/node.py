from twisted.internet import reactor

from util import Framework
from consensusProtocols.TPC.TwoPhaseCommit import TwoPhaseCommit

import optparse


def parse_args():
  usage = """usage: %prog [options] [hostname:]port

This is the framework node, run like this:

  python node.py [option] <host ip and port to listen>
"""
  
  parser = optparse.OptionParser(usage)
  
  help = "The address and port to connect to, in [ip:]port format"
  parser.add_option('--connect', type='string', help=help, default=0)
  help = "The logfile location"
  parser.add_option('--logfile', type='string', help=help, default='log.log')
  help = "The database location"
  parser.add_option('--db', type='string', help=help, default='database.db')
  help = "The replica name"
  parser.add_option('--name', type='string', help=help, default='1')
  
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

def main():
  import consensus
  opt = parse_args()
  protocol = Framework((opt.host, opt.port),
                       (opt.master_host, opt.master_port),
                       opt.logfile)
  #protocol.setAlgorithm(consensus.Default())
  protocol.setAlgorithm(TwoPhaseCommit(opt.name, opt.db))
  protocol.run()

if __name__ == "__main__":
  main()

