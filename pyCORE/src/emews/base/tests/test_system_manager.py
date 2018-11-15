"""
Unit test module - system_manager.py.

Created on November 15, 2018
@author: Brian Ricks
"""
import logging
from unittest import TestCase

import emews.base.baseobject
import emews.base.config
import emews.base.system_init
import emews.base.system_manager


class SystemManagerTest(TestCase):
    """
    Unit tests for system_init.py.
    """

    def setUp(self):
        """Stuff that may be needed in unit tests."""
        self.args = emews.base.config.Config({
            'sys_config': 'base/tests/sample_conf_2.yml',
            'node_config': None,
            'node_name': 'TestNode'
        })

    def test_system_manager(self):
        """
        Unit test for SystemManager class.
        """
        # check when using daemon mode (required as this is what launches the System Manager)
        # using self.args for the args
        system_manager = emews.base.system_init.system_init(self.args)
        self.assertIsInstance(system_manager, emews.base.system_manager.SystemManager)

        self._check_config_dict(config_dict)

        self.assertIsNone(config_dict['startup_services'])

        # using self.args2 for the args (explicit node config yaml)
        config_dict = emews.base.system_init.system_init(self.args2, is_daemon=False)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name,
                         'test_node_conf')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        self._check_config_dict(config_dict)
