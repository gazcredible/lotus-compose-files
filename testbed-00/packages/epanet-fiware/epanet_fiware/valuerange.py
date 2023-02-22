class ValueRange(dict):
    def __init__(self, _min=float('inf'), _max=float('-inf')):
        dict.__init__(self, minval=_min, maxval=_max)

    def add(self, val):
        if val < self.getvalue('minval'):
            self.setvalue('minval', val)

        if val > self.getvalue('maxval'):
            self.setvalue('maxval', val)

    def get(self, val):
        return ((val-self.__dict__['min']) / (
            self.__dict__['max'] - self.__dict__['min']))

    def getvalue(self, label):
        return super(ValueRange, self).__getitem__(label)

    def setvalue(self, label, value):
        return super(ValueRange, self).__setitem__(label, value)
