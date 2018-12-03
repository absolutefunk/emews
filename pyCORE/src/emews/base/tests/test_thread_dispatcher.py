"""
Unit test module - thread_dispatcher.py.

Created on December 3, 2018
@author: Brian Ricks
"""
from unittest import TestCase

import emews.base.thread_dispatcher


class ThreadDispatcherTest(TestCase):
    """
    Unit tests for system_init.py.
    """

    def setUp(self):
        """Stuff that may be needed in unit tests."""
        self.config1 = {
            'thread_shutdown_wait': 1.0,
            'service_start_delay': 2.0
        }

    def test_system_init(self):
        """
        Unit test for system_init() function
        """
        # 1 ##
        thr_dispatcher = emews.base.thread_dispatcher.ThreadDispatcher(self.config1)
