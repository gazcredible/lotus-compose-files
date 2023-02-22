class ChartingSupport():
    def __init__(self):
        self.init()

    def init(self):
        self.graph_max = -999999
        self.graph_min = 999999
        self.limit_is_max = False
        self.limit_is_min = False

    def add_value(self, value:float, is_limit:bool=False):
        if value is not None:
            if float(value) > self.graph_max:
                self.graph_max = float(value)
                if is_limit:
                    self.limit_is_max = True

            if float(value) < self.graph_min:
                self.graph_min = float(value)
                if is_limit:
                    self.limit_is_min = True

    def get_range(self) -> dict:
        if self.limit_is_max:
            self.graph_max *= 1.1

        if self.limit_is_min:

            if self.graph_min == 0:
                self.graph_min = -(self.graph_max * 0.05)
            else:
                self.graph_min -= (self.graph_max - self.graph_min) * 0.1

        return {'min': self.graph_min, 'max': self.graph_max}



