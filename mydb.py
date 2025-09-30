import os.path
import pickle

class MyDB:

    def __init__(self, filename):
        self.fname = filename
        if not os.path.isfile(self.fname):
            self.saveStrings([])

    def loadStrings(self):
        with open(self.fname, 'rb') as f:
            arr = pickle.load(f)
        return arr

    def saveStrings(self, arr):
        with open(self.fname, 'wb') as f:
            pickle.dump(arr, f)

    def saveString(self, s):
        arr = self.loadStrings()
        arr.append(s)
        self.saveStrings(arr)
