from sfl_diagnoser.Diagnoser.Singelton import Singleton

class Experiment_Data(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.TERMINAL_PROB = 0.7
        self.PRIORS = []
        self.BUGS = []
        self.POOL = {}
        self.ESTIMATED_POOL = {}
        self.COMPONENTS_NAMES = {}
        self.clear()

    def clear(self):
        self.PRIORS = []
        self.BUGS = []
        self.POOL = {}
        self.COMPONENTS_NAMES = {}

    def set_values(self, priors_arg, bugs_arg, pool_arg, components_arg, extimated_pool_arg=None):
        self.clear()
        self.PRIORS = priors_arg
        self.BUGS = bugs_arg
        self.POOL = pool_arg
        self.COMPONENTS_NAMES = components_arg
        self.ESTIMATED_POOL = extimated_pool_arg

    def get_named_bugs(self):
        return map(lambda id: Experiment_Data().COMPONENTS_NAMES[id], Experiment_Data().BUGS)

if __name__ == "__main__":
    a = Experiment_Data()
    b = Experiment_Data()
    pass