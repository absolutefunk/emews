'''
Base class for pyCORE service decorators.
Subclasses when overriding the required methods can use super(cls, self) to access the methods
being overridden.

Created on Mar 30, 2018

@author: Brian Ricks
'''
import emews.core.services.iservice

class ServiceDecorator(emews.core.services.iservice.IService):
    '''
    classdocs
    '''
    def __init__(self, recipient_service):
        '''
        Constructor
        '''
        self._recipient_service = recipient_service
        # cache a reference to the decorator config, if it exists
        self._decorator_config = self._recipient_service.config.extract_with_key(
            'decorators', self.__class.__name__)

        self.logger.info("Added decorator '%s' to %s.", self.__class__.__name__,
                         recipient_service.name)

    @property
    def config(self):
        '''
        @Override Returns the decorator specific config options, if exists.
        Convenience property as the config options exist in the service config and can be
        obtained from self.config.
        '''
        return self._decorator_config

    @property
    def logger(self):
        '''
        @Override Returns the logger object used with the recipient_service.
        '''
        return self._recipient_service.logger

    @property
    def interrupted(self):
        '''
        Returns true if the service has been interrupted (requested to stop).  Use implementaton
        from recipient_service.
        '''
        return self._recipient_service.interrupted

    @property
    def service_config(self):
        '''
        Returns the recipient_service config.  Convenience property.
        '''
        return self._recipient_service.config

    def sleep(self, time):
        '''
        @Override calls the sleep implementaton of recipient_service.
        '''
        self._recipient_service.sleep(time)

    def start(self):
        '''
        @Override Starts the service.
        '''
        self._recipient_service.start()

    def stop(self):
        '''
        @Override Gracefully exit service
        '''
        self._recipient_service.stop()

    def importclass(self, class_name, module_path):
        '''
        @Override Import a class, given the class name and module path.  Use emews naming
        conventions, in that the class to import will have the same name as the module (class name
        converted to lower case automatically for module).  This method calls the same method from
        the recipient_service.
        '''
        return self._recipient_service.importclass(class_name, module_path)
