from Components.Converter.Converter import Converter
from Components.Element import cached
from os.path import exists

class GOSopkgUpgrade(Converter, object):

    def __init__(self, arg):
        Converter.__init__(self, arg)

    @cached
    def getBoolean(self):
        localVersionFile = '/tmp/gos_upd'
        if exists(localVersionFile):
            return True
        else:
            return False

    boolean = property(getBoolean)

    def changed(self, what):
        Converter.changed(self, what)
