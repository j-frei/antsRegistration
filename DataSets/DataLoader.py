from abc import ABC, abstractmethod

class DataSet(ABC):
   @abstractmethod
   def getFilePaths(self):
      pass
   @abstractmethod
   def getFileIDs(self):
      pass
   @abstractmethod
   def getDataSetPrefix(self):
       pass
   @abstractmethod
   def loadVol(self,path_file):
      pass
   def alignToAtlas(self,vol,atlas):
       return vol


