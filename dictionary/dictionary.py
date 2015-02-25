#This file acts as a key value datastore
#this class's object could be synchronized
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
    #These static methods can be called with class-name.method name
    @staticmethod
    def put(k,v):
        dictionary.instantiation().putInternal(k,v)
        
    
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
        

    @staticmethod
    def get(k):
        return dictionary.instantiation().getInternal(k)
    
    def getInternal(self,k):
        return dictionary.dictObj.get(k)
    
    def writeToFile(self):
        #conversion of dictionary object to json string
        jsonstring=json.dumps(dictionary.dictObj)
        #just clearing file before writing anything to it
        open('keyvaluestore.txt', 'w').close()
        #writing a json string
        with open('keyvaluestore.txt', 'w') as f:
            f.write(jsonstring)
        
    #this is the constructor. It reads file and loads all data into dictionary object   
    def __init__(self, file_path='keyvaluestore.txt'):
        self.file_path = file_path
        try:
            with open (self.file_path, "r") as myfile:
                jsonstring=myfile.readline()
        except IOError:
            print("file did not exist and hence it will be created")
            with open (self.file_path, "w+") as myfile:
                jsonstring=myfile.readline()
        if os.stat(self.file_path).st_size != 0:
            dictionary.dictObj = json.loads(jsonstring)
            

     