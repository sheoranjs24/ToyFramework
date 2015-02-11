#This file acts as a key value datastore
#this class's object should be synchronized
import json
import os

class dictionary(object):
    
    dictObj={}
    
    flagForObjInstantiation=0
    
    classObj = {}
    
    #This method is called from various static methods to make sure that this class has
    #only one object
    @staticmethod
    def instantiation():
        if dictionary.flagForObjInstantiation == 0:
                dictionary.classObj = dictionary()
                flagForObjInstantiation = 1
                return dictionary.classObj
        else:
            return classObj
    
    def returnClassObj(self):
        return classObj
    #static methods are exposed. One can call these methods with class-name.method name
    @staticmethod
    def put(k,v):
        dictionary.instantiation().putInternal(k,v)
        
    #these internal methods are not exposed
    def putInternal(self,k,v):
        dictionary.dictObj.update({k:v})
        dictionary.classObj.writeToFile()
        
    @staticmethod   
    def delete(k):
        dictionary.instantiation().deleteInternal(k)
        
    def deleteInternal(self,k):
        try:
            dictionary.dictObj.pop(k)
        except KeyError:
            print "Sorry key not found, Hence element not popped"
        dictionary.classObj.writeToFile()
        #todo call internal fn

    @staticmethod
    def get(k):
        return dictionary.instantiation().getInternal(k)
    
    def getInternal(self,k):
        return dictionary.dictObj.get(k)
    
    def writeToFile(self):
        #conversion of dictionary object to json string
        jsonstring=json.dumps(dictionary.dictObj)
        #just clearing file before writing anything to it
        open('file.txt', 'w').close()
        #writing a json string
        with open('file.txt', 'w') as f:
            f.write(jsonstring)
        
     #this is the constructor. It reads file and loads all data into dictionary object   
    def __init__(self):
        try:
            with open ("file.txt", "r") as myfile:
                jsonstring=myfile.readline()
        except IOError:
            print("file did not exist and hence it will be created")
            with open ("file.txt", "w+") as myfile:
                jsonstring=myfile.readline()
        if os.stat("file.txt").st_size != 0:
            dictionary.dictObj = json.loads(jsonstring)
            

     