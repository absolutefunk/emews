import abc


class InjectionMeta(type):
    """
    Meta class for class attribute dependency injection.

    Dependency injection is performed before any child class __init__ methods are called.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        """Override __init__ in subclass with below definition."""
        new_cls = super(InjectionMeta, mcs).__new__(mcs, name, bases, namespace, **kwargs)
        # store a reference to the subclass __init__
        subcls_init = new_cls.__init__

        def __init__(self, *args, **kwargs):
            """
            Injected Constructor from MetaInjection.

            Used to inject configuration before the original subclass __init__ is called.  This way
            the configuration is available without the dev having to explicitly handle a config
            object on __init__.
            """
            if '_inject' in kwargs:
                # pop the key so the class doesn't get it through **kwargs
                inject_dict = kwargs.pop('_inject')
                # these are class-specific attributes, could be anything
                for attr_name, attr_value in inject_dict.iteritems():
                    setattr(self, attr_name, attr_value)

            subcls_init(self, *args, **kwargs)

        setattr(new_cls, '__init__', __init__)  # replace subclass init with this one
        return new_cls


# Composition of InjectionMeta and ABCMeta
InjectionMetaWithABC = type('InjectionMetaWithABC', (abc.ABCMeta, InjectionMeta), {})
