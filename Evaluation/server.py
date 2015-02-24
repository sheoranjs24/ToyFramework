import pyro4
from dictionary import dictionary


def main():
    data_store = dictionary()
    Pyro4.Daemon.serveSimple(
            {
                data_store: "example.datastore"
            },
            ns = False)

if __name__=="__main__":
    main()