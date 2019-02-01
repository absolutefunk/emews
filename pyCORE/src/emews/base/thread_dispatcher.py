"""
Handles thread management.  Acts as a dispatcher for threads.

Created on Mar 30, 2018
@author: Brian Ricks
"""
import threading
import weakref

import emews.base.baseobject
import emews.base.threadwrapper


def thread_names_str():
    """Concatenates active thread names to a space delim string."""
    thread_names = []
    for thread in threading.enumerate():
        thread_names.append(thread.name)

    return ", ".join(thread_names)


class ThreadDispatcher(emews.base.baseobject.BaseObject):
    """Dispatches and manages active threads."""

    __slots__ = ('_active_threads', '_deferred_threads', '_delay_timer', '_delay_lock',
                 '_thread_shutdown_timeout')
    __dispatch_timer_id = 0  # each timer has a unique thread id in the name

    def __init__(self, config):
        """Constructor."""
        super(ThreadDispatcher, self).__init__()

        # When a thread dies, it is automatically removed from the _active_threads set.
        self._active_threads = weakref.WeakSet()
        self._deferred_threads = set()

        self._delay_timer = None
        self._delay_lock = threading.Lock()

        self._thread_shutdown_timeout = config['thread_shutdown_wait']
        if self._thread_shutdown_timeout <= 0:
            self._thread_shutdown_timeout = None

        if not self.sys['local']:
            start_delay = config['service_start_delay']
            if start_delay > 0:
                self.logger.info("Beginning service start delay of %d seconds.", start_delay)
                self.delay_dispatch(start_delay)
        else:
            self.logger.info("Service start delay ignored due to running in local mode.")

    @property
    def count(self):
        """Return a count of active threads."""
        return len(self._active_threads)

    def join(self):
        """Join all active threads."""
        for active_thread in self._active_threads:
            active_thread.join()

    def dispatch_thread(self, object_instance, force_start=False):
        """
        Create and dispatches a new ThreadWrapper.

        object_instance is the object that we want to wrap around ThreadWrapper.  If 'force_start'
        is True, then dispatch thread anyway.
        """
        if not force_start:
            # The lock is required here as the timer could clear the self._delay_timer instance
            # right after we check it here, resulting possibly in a deferred thread that is never
            # started.
            with self._delay_lock:
                if self._delay_timer is not None:
                    wrapped_object = emews.base.threadwrapper.ThreadWrapper(
                        object_instance, autostart=False)
                    self.logger.debug("Thread '%s' deferred for dispatching.", wrapped_object.name)
                    self._deferred_threads.add(wrapped_object)
                    return

        wrapped_object = emews.base.threadwrapper.ThreadWrapper(object_instance)
        # we also need to store the thread reference itself, so shutting down all threads we can
        # join each thread
        self._active_threads.add(wrapped_object)

        self.logger.info("Dispatched thread '%s'.", wrapped_object.name)
        self.logger.debug("Active dispatched thread count: %d", self.count)
        self.logger.debug("Active threads: %s", thread_names_str())

    def dispatch_deferred_threads(self):
        """Dispatch threads which have been deferred for execution."""
        for wrapped_object in self._deferred_threads:
            self.logger.info("Dispatched thread '%s'.", wrapped_object.name)
            wrapped_object.start()
            self._active_threads.add(wrapped_object)

        if self._deferred_threads > 0:
            self.logger.debug("Dispatched all deferred threads.")
            self._deferred_threads.clear()
            self.logger.debug("Active dispatched thread count: %d", self.count)
            self.logger.debug("Active threads: %s", thread_names_str())
        else:
            self.logger.debug("No deferred threads to dispatch.")

    def delay_dispatch(self, delay_time):
        """
        Delay dispatch of any threads until 'delay_time' has elapsed.

        Delay begins once delay_timer is started.
        """
        self._delay_timer = threading.Timer(
            delay_time, self._finished_delay_cb)
        self._delay_timer.name = 'dispatch_timer_' + str(ThreadDispatcher.__dispatch_timer_id)
        ThreadDispatcher.__dispatch_timer_id += 1
        self._delay_timer.start()

    def _finished_delay_cb(self):
        """Invoke when delay (delay_timer) is finished."""
        # As this callback will run in the Timer thread, we acquire the lock only if there is not
        # a thread in the middle of being added to the deferred set.
        with self._delay_lock:
            self._delay_timer = None
            self.dispatch_deferred_threads()

        return

    def shutdown_all_threads(self):
        """Shut down all running threads."""
        # We need the lock to make sure the Timer instance doesn't clear between checking for None
        # and invoking cancel().
        with self._delay_lock:
            if self._delay_timer is not None:
                self.logger.debug("Delay dispatch timer is active, cancelling timer ...")
                self._delay_timer.cancel()
                self._delay_timer.join()

        self.logger.info("%d dispatched thread(s) to shutdown.", self.count)

        if self.count > 0:
            for active_thread in self._active_threads:
                active_thread.stop()

            if self._thread_shutdown_timeout is not None:
                self.logger.info("Will wait a maximum of %d seconds for threads to shutdown.",
                                 self._thread_shutdown_timeout)
            else:
                self.logger.info("No thread join timeout set.  Will wait until all running "
                                 "threads shut down ...")

            for active_thread in self._active_threads:
                # Wait for each service to shutdown.  We put this in a separate loop so each service
                # will get the shutdown request first, and can shutdown concurrently.
                active_thread.join(timeout=self._thread_shutdown_timeout)

            # check if any threads are still running
            if self._thread_shutdown_timeout is not None and self.count > 0:
                thread_names = []
                for thr in self._active_threads:
                    thread_names.append(thr.name)

                thr_names_str = ", ".join(thread_names)
                self.logger.warning("The following threads did not shut down within the timeout "
                                    "period: [%s].  Shutdown proceeding ...", thr_names_str)
