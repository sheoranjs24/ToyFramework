
import Pyro4
from dictionary import dictionary, ResourceManager
import client

data_store = dictionary()
user1 = client("user1", data_store)

print user1.get('key1')
print user1.delete('key1')