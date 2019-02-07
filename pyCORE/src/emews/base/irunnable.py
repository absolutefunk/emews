"""
Interface for classes that need to be runnable through the ThreadWrapper.

Even though Python is duck typed, and this interface really doesn't do much in practice, it helps
during coding to make sure that the programmer (me) is aware if they (me) forget to implement a
method as part of this contract.

Created on Apr 11, 2018
@author: Brian Ricks
"""
import abc

# Python 2.7 does not contain __slots__ in the ABCMeta class definition, which we need.
ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class IRunnable(ABC):
    """Classdocs."""

    __slots__ = ()

    @abc.abstractproperty
    def interrupted(self):
        """Interrupted state of the service."""
        pass

    @abc.abstractmethod
    def stop(self):
        """Signal that the implementing class needs to gracefully exit all tasks."""
        pass

    @abc.abstractmethod
    def start(self):
        """Start execution of implementing task."""
        pass
