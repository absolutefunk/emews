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
import emews.base.system_manager


class SystemInitTest(TestCase):
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

        # using a node config
        self.args2 = emews.base.config.Config({
            'sys_config': 'base/tests/sample_conf_2.yml',
            'node_config': 'base/tests/sample_nodeconfig.yml',
            'node_name': None
        })

        # using no node config or node name
        self.args3 = emews.base.config.Config({
            'sys_config': 'base/tests/sample_conf_2.yml',
            'node_config': None,
            'node_name': None
        })

    def test_system_init(self):
        """
        Unit test for system_init() function
        """
        # test when not launching in daemon mode
        # using self.args for the args
        config_dict = emews.base.system_init.system_init(self.args, is_daemon=False)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name, 'TestNode')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

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

        self.assertIn('logserver', config_dict['startup_services'])
        self.assertIsNone(config_dict['startup_services']['logserver'])

        # no node name defined
        # using self.args3 for the args
        config_dict = emews.base.system_init.system_init(self.args3, is_daemon=False)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name)
        self.assertIsInstance(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name,
                              basestring)
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        self._check_config_dict(config_dict)

        self.assertIn('logserver', config_dict['startup_services'])
        self.assertIsNone(config_dict['startup_services']['logserver'])

        # check when using daemon mode
        # using self.args for the args
        system_manager = emews.base.system_init.system_init(self.args)
        self.assertIsInstance(system_manager, emews.base.system_manager.SystemManager)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name, 'TestNode')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        # check when using daemon mode
        # using self.args2 for the args
        system_manager = emews.base.system_init.system_init(self.args2)
        self.assertIsInstance(system_manager, emews.base.system_manager.SystemManager)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name,
                         'test_node_conf')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        # check when using daemon mode
        # using self.args3 for the args
        system_manager = emews.base.system_init.system_init(self.args3)
        self.assertIsInstance(system_manager, emews.base.system_manager.SystemManager)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name)
        self.assertIsInstance(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name,
                              basestring)
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

    def _check_config_dict(self, config_dict):
        """
        check system properties
        """

        # check the config_dict for K/Vs common to all testing scenarios
        self.assertIsInstance(config_dict, dict)
        self.assertIn('general', config_dict)
        self.assertIn('service_start_delay', config_dict['general'])
        self.assertEqual(config_dict['general']['service_start_delay'], 300)
        self.assertIn('thread_shutdown_wait', config_dict['general'])
        self.assertEqual(config_dict['general']['thread_shutdown_wait'], 5)

        self.assertIn('communication', config_dict)
        self.assertIn('host', config_dict['communication'])
        self.assertEqual(config_dict['communication']['host'], 'localhost')
        self.assertIn('port', config_dict['communication'])
        self.assertEqual(config_dict['communication']['port'], 32518)

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
