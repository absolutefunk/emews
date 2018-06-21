'''
Manages the eMews daemon execution.
'''
import emews.base.baseobject

class SystemManager(emews.base.baseobject.BaseObject):
    '''
    classdocs
    '''
    def __init__(self, config):
        '''
        Constructor
        '''
        super(SystemManager, self).__init__(config)
        self.logger.debug("Starting system manager ...")

    def _startup_services(self):
        '''
        Looks in the config object to obtain any services present.
        '''
