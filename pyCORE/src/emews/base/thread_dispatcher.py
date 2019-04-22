"""
Handles thread management.  Acts as a dispatcher for threads.

Created on Mar 30, 2018
@author: Brian Ricks
"""
import os
import threading
import signal

import emews.base.baseobject


def thread_names_str():
    """Concatenates active thread names to a space delim string."""
    thread_names = []
    for thread in threading.enumerate():
        thread_names.append(thread.name)

    return ", ".join(thread_names)


class ThreadDispatcher(emews.base.baseobject.BaseObject):
    """Dispatches and manages active threads."""

    __dispatch_timer_id = 0  # each timer has a unique thread id in the name
    __thread_id = 0  # each thread has a unique id
    __dispatch_id = 0  # for unique dispatchers
    __slots__ = ('_thread_map', '_deferred_objects', '_delay_timer', '_delay_lock',
                 '_thread_shutdown_timeout', '_halt_on_exceptions', '_dispatcher_name',
                 '_service_count')

    def __init__(self, config):
        """Constructor."""
        super(ThreadDispatcher, self).__init__()

        self._dispatcher_name = "Dispatcher" + str(ThreadDispatcher.__dispatch_id)
        ThreadDispatcher.__dispatch_id += 1

        self._thread_map = {}  # object and its corresponding thread
        self._deferred_objects = set()
        self._service_count = 0  # current active service count

        self._delay_timer = None
        self._delay_lock = threading.Lock()

        self._thread_shutdown_timeout = config['thread_shutdown_wait']
        if self._thread_shutdown_timeout <= 0:
            self._thread_shutdown_timeout = None

        self._halt_on_exceptions = config['halt_on_service_exceptions']

        if not self.sys.local:
            start_delay = config['service_start_delay']
            # NOTE: service start delay currently delays all objects
            if start_delay > 0:
                self.logger.info("Beginning service start delay of %d seconds.", start_delay)
                self.delay_dispatch(start_delay)
        else:
            self.logger.info("Service start delay ignored due to running in local mode.")

    def __str__(self):
        """Return the dispatcher name."""
        return self._dispatcher_name

    @property
    def count(self):
        """Return a count of active threads."""
        return threading.active_count() - 1

    def cb_thread_exit(self, object_instance, on_exception=False):
        """Unregisters an object that has terminated."""
        if hasattr(object_instance, 'service_id'):
            self._service_count -= 1

        if on_exception:
            self.logger.error(
                "Object '%s' has expressed intent to terminate due to exception.",
                str(object_instance))
            if self._halt_on_exceptions:
                self.logger.info("Halt-on-exceptions enabled, throwing SIGINT ...")
                os.kill(os.getpid(), signal.SIGINT)
        else:
            self.logger.debug(
                "Object '%s' has expressed intent to terminate.", str(object_instance))

    def dispatch(self, object_instance, force_start=False):
        """
        Create and possibly dispatch object_instance contained in a thread.

        object_instance is the object that we want to wrap in a Thread.  If 'force_start'
        is True, then dispatch thread anyway.
        """
        if not force_start:
            # The lock is required here as the timer could clear the self._delay_timer instance
            # right after we check it here, resulting possibly in a deferred thread that is never
            # started.
            with self._delay_lock:
                if self._delay_timer is not None:
                    self._deferred_objects.add(object_instance)
                    self.logger.debug("'%s' deferred for dispatching.", str(object_instance))
                    return

        self._object_dispatch(object_instance)
        self._dispatch_info()

    def _object_dispatch(self, object_instance):
        """Dispatch an object instance."""
        object_instance.register_dispatcher(self)

        new_thread = threading.Thread(
            name=str(object_instance) + '_' + str(ThreadDispatcher.__thread_id),
            target=object_instance.start)

        ThreadDispatcher.__thread_id += 1
        self._thread_map[object_instance] = new_thread
        new_thread.setDaemon(True)
        new_thread.start()

        self.logger.info("Dispatched thread '%s'.", new_thread.name)

        if hasattr(object_instance, 'service_id'):
            self._service_count += 1

    def _dispatch_info(self):
        """Display dispatch stats."""
        self.logger.debug("Active dispatched thread count: %d", self.count)
        self.logger.debug("Active threads: %s", thread_names_str())

    def dispatch_deferred_objects(self):
        """Dispatch objects which have been deferred for execution."""
        if not len(self._deferred_objects):
            self.logger.debug("No deferred threads to dispatch.")
            return

        for object_instance in self._deferred_objects:
            self._object_dispatch(object_instance)

        self.logger.debug("Dispatched all deferred threads.")
        self._deferred_objects.clear()
        self._dispatch_info()
        self.logger.info("Active services: %d", self._service_count)

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
            self.dispatch_deferred_objects()

        return

    def shutdown_all_threads(self):
        """Shut down all running threads."""
        # We need the lock to make sure the Timer instance doesn't clear between checking for None
        # and invoking cancel().
        if threading.current_thread().__class__.__name__ != '_MainThread':
            err_msg = "Must call 'shutdown_all_threads()' from MainThread."
            self.logger.error(err_msg)
            raise RuntimeError(err_msg)

        with self._delay_lock:
            if self._delay_timer is not None:
                self.logger.debug("Delay dispatch timer is active, cancelling timer ...")
                self._delay_timer.cancel()
                self._delay_timer.join()

        self.logger.info("%d dispatched thread(s) to shutdown.", self.count)

        if self.count > 0:
            for t_object in self._thread_map.keys():
                # send stop requests to all registered objects
                t_object.interrupt()

            if self._thread_shutdown_timeout is not None:
                self.logger.info("Will wait a maximum of %d seconds for threads to shutdown.",
                                 self._thread_shutdown_timeout)
            else:
                self.logger.info("No thread join timeout set.  Will wait until all running "
                                 "threads shut down ...")

            for active_thread in threading.enumerate():
                # join all active threads except for the main thread
                if active_thread is not threading.current_thread():
                    # current_thread is main thread
                    active_thread.join(timeout=self._thread_shutdown_timeout)

            # check if any threads are still running
            if self._thread_shutdown_timeout is not None and self.count > 0:
                thread_names = []
                for active_thread in threading.enumerate():
                    if active_thread is not threading.current_thread() and active_thread.isAlive():
                        thread_names.append(active_thread.name)

                if len(thread_names) > 0:
                    thr_names_str = ", ".join(thread_names)
                    self.logger.warning(
                        "The following threads did not shut down within the timeout period: [%s].  "
                        "Shutdown proceeding ...", thr_names_str)
