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
            'sys_config': 'base/tests/sample_conf.yml',
            'node_config': None,
            'node_name': 'TestNode'
        })

    def test_system_init(self):
        '''
        Unit test for system_init() function
        '''
        # test when not launching in daemon mode
        config_dict = emews.base.system_init.system_init(self.args, is_daemon=False)

        # check system properties
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name, 'TestNode')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        # check the config_dict
        # many of these checks are similar to those in test_config, but complete
        self.assertIsInstance(config_dict, dict)
        self.assertIn('general', config_dict)
        self.assertIn('service_start_delay', config_dict['general'])
        self.assertEqual(config_dict['general']['service_start_delay'], 300)

        self.assertIn('logging', config_dict)
        self.assertIn('logger', config_dict['logging'])
        self.assertEqual(config_dict['logging']['logger'], 'emews.distributed')
        self.assertIn('message_level', config_dict['logging'])
        self.assertEqual(config_dict['logging']['message_level'], 'DEBUG')
        self.assertIn('logger_parameters', config_dict['logging'])
        self.assertIsInstance(config_dict['logging']['logger_parameters'], dict)
        self.assertIn('host', config_dict['logging']['logger_parameters'])
        self.assertEqual(config_dict['logging']['logger_parameters']['host'], '10.0.0.21')
        self.assertIn('port', config_dict['logging']['logger_parameters'])
        self.assertEqual(config_dict['logging']['logger_parameters']['host'], 32519)

        self.assertIn('startup_services', config_dict)
        self.assertIsNone(config_dict['startup_services'])
