__all__ = ['BorgCounter', 'DejaVue']


class BorgCounter():
    '''
    A class that implements a static global counter.
    Instances of this class all share the same global counter.
    This is used in DictReader class to assure that multiple instances
    of CppDict do not generate conflicting IDs for placeholder strings
    (as would be the case otherwise when merging included dicts).
    '''
    Borg = {'theCount': -1}

    def __init__(self):
        self.__dict__ = BorgCounter.Borg
        # self.theCount = -1

    def __call__(self):
        self.theCount += 1
        #   Small tweak for our use case: As we have only six digits available in our placeholder strings,
        #   we don't want the counter to exceed this. Fair to start again at 0 then :-)
        if self.theCount > 999999:
            self.theCount = 0
        return self.theCount

    @staticmethod
    def reset():
        BorgCounter.Borg['theCount'] = -1


class DejaVue():
    '''
    return True if string repeats after initializing class
    '''
    djv = {'strings': [], 'retVal': False}

    def __init__(self):
        self.__dict__ = DejaVue.djv

    def __call__(self, string):

        if string in self.djv['strings']:
            self.djv['retVal'] = True

        self.djv['strings'].append(string)

        return self.djv['retVal']

    @property
    def strings(self):
        return self.djv['strings']

    def reset(self):
        self.djv['strings'] = []
        self.djv['retVal'] = False
