"""
Configuration related module.

Created on Apr 3, 2018
@author: Brian Ricks
"""
from ruamel.yaml import YAML


def parse(filename):
    """Parse the given filename (if it exists), and returns a dictionary."""
    if filename is None:
        return None

    f = open(filename)

    yaml = YAML()
    dct = yaml.load(f)

    return dct

# TODO: possibly move this to another module
class InjectionMeta(type):
    """
    Meta class for configuration dependency injection.

    Dependency Injection is performed before any child class __init__ methods are called.
    Config object injected through constructor, but processed first using an __init__ override.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        """Override __init__ in subclass with below definition."""
        new_cls = super(InjectionMeta, mcs).__new__(mcs, name, bases, namespace, **kwargs)
        # store a reference to the subclass __init__
        subcls_init = new_cls.__init__

        def __init__(self, *args, **kwargs):
            """
            Injected Constructor from InjectionMeta.

            Used to inject configuration before the original subclass __init__ is called.  This way
            the configuration is available without the dev having to explicitly handle a config
            object on __init__.
            """
            # As a derived class could pass their own '_inject' k/v, we not only check for the key,
            # but whether the _config attribute exists already.
            if '_inject' in kwargs and not hasattr(self, '_di_config'):
                # pop the key so the class doesn't get it through **kwargs
                inject_dict = kwargs.pop('_inject')
                # 'config' is a required key
                self._di_config = inject_dict['config']  # pylint: disable=W0212
                # optional keys
                if 'helpers' in inject_dict:
                    self._di_helpers = inject_dict['helpers']  # pylint: disable=W0212
                if 'extra' in inject_dict:
                    # these are class-specific attributes, could be anything
                    for attr_name, attr_value in inject_dict['extra']:
                        setattr(self, attr_name, attr_value)

            subcls_init(self, *args, **kwargs)

        setattr(new_cls, '__init__', __init__)  # replace subclass init with this one
        return new_cls

# TODO: possibly move this to another module
class DelayedInstantiation(object):
    """For objects that do not instantiate immediately."""

    __slots__ = ('_cls', '_config', '_container', '_container_key')

    def __init__(self, cls, cls_config):
        """Constructor."""
        self._cls = cls
        self._config = cls_config
        self._container = None
        self._container_key = None

    def set_container(self, container, key):
        """
        Set the container object in which this object resides.

        The key is used to lookup this object from the container.
        """
        self._container = container
        self._container_key = key

    def __call__(self):
        """
        Instantiate the class instance passed during construction.

        Also replace the instance key in the container (Config) with the instantiated object.
        """
        if self._container is None:
            raise ValueError("Cannot instantiate class as container is not known")
        if self._container_key is None:
            raise ValueError("Cannot instantiate class as container key is not known")

        obj_instance = self._cls(_inject={'config': self._config})
        self._container.__dict__[self._container_key] = obj_instance


class Config(object):
    """Provides a very simple config object using both dot and index notation."""

    # What, no slots??  Yep, as it turns out, dict access performance is on par with slots,
    # and memory is a bit better using a dict as we can define the class once, instead of
    # needing to have a separate class definition for each eMews object type.

    def __init__(self, config_dict):
        """Constructor."""
        # The magic __dict__ stores all our instance fields, so this is a quick way of assigning
        # the K/Vs from dct.
        self._assign_dict(config_dict)
        # convert nested dicts to Config objects
        for key, value in self.__dict__.items():
            if isinstance(value, dict):
                # First check if this dict is actually for a delayed instantiation helper.
                if len(value) == 1 and 'instantiate' in value and \
                        isinstance(value['instantiate'], DelayedInstantiation):
                    # Give this Config self to the DelayedInstantiation object, and the key to
                    # look it up.
                    value['instantiate'].set_container(self, key)

                # replace with Config object
                self.__dict__[key] = Config(value)

    def _assign_dict(self, dict):
        """
        Assign K/Vs of input dict to self.__dict__.

        This is performed in case the input dict is of some custom dict type.
        """
        self.__dict__ = {}
        for key, val in dict.items():
            self.__dict__[key] = val

    def __contains__(self, key):
        """Enable 'in' shorthand."""
        return key in self.__dict__

    def __getitem__(self, key):
        """Enable index notation for getting attributes."""
        return self.__dict__[key]

    def __len__(self):
        """Return number of K/Vs in the __dict__ of this object."""
        return len(self.__dict__)
