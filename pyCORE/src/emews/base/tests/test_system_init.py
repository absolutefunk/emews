"""
Unit test module - system_init.py.

Created on October 17, 2018
@author: Brian Ricks
"""
import logging
from unittest import TestCase

import emews.base.baseobject
import emews.base.config
import emews.base.system_init


class SystemInitTest(TestCase):
    """
    Unit tests for system_init.py.
    """

    def setUp(self):
        """Stuff that may be needed in unit tests."""
        self.args = emews.base.config.Config({
            'sys_config': None,
            'node_config': None,
            'node_name': 'TestNode'
        })

    def test_system_init(self):
        '''
        Unit test for system_init() function
        '''
        # test when not launching in daemon mode
        system_init = emews.base.system_init.system_init(self.args, is_daemon=False)

        # check system properties
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name, 'TestNode')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)
