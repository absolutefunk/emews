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
            'sys_config': 'base/tests/sample_conf.yml',
            'node_config': None,
            'node_name': 'TestNode'
        })

        # using a node config
        self.args2 = emews.base.config.Config({
            'sys_config': 'base/tests/sample_conf.yml',
            'node_config': 'base/tests/sample_nodeconfig.yml',
            'node_name': None
        })

        # using no node config or node name
        self.args3 = emews.base.config.Config({
            'sys_config': 'base/tests/sample_conf.yml',
            'node_config': None,
            'node_name': None
        })

        # using a node config and node name
        self.args4 = emews.base.config.Config({
            'sys_config': 'base/tests/sample_conf.yml',
            'node_config': 'base/tests/sample_nodeconfig.yml',
            'node_name': 'TestNode'
        })

    def test_system_init(self):
        """
        Unit test for system_init() function
        """
        # 1 ##
        # using self.args for the args
        sys_manager = emews.base.system_init.system_init(self.args)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name, 'TestNode')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        self._check_config_dict(sys_manager._config)

        self.assertIsNone(sys_manager._config['startup_services'])

        # 2 ##
        # using self.args2 for the args (explicit node config yaml)
        sys_manager = emews.base.system_init.system_init(self.args2)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name,
                         'test_node_conf')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        self._check_config_dict(sys_manager._config)

        self.assertIn('testservice', sys_manager._config['startup_services'])
        self.assertIsNone(sys_manager._config['startup_services']['testservice'])

        # 3 ##
        # no node name defined
        # using self.args3 for the args
        sys_manager = emews.base.system_init.system_init(self.args3)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name)
        self.assertIsInstance(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name,
                              basestring)
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        self._check_config_dict(sys_manager._config)

        self.assertIsNone(sys_manager._config['startup_services'])

        # 4 ##
        # using self.args4 for the args (explicit node config yaml)
        sys_manager = emews.base.system_init.system_init(self.args4)

        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES)
        self.assertIsInstance(
            emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.logger, logging.LoggerAdapter)
        self.assertEqual(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.node_name,
                         'TestNode')
        self.assertIsNotNone(emews.base.baseobject.BaseObject._SYSTEM_PROPERTIES.root)

        self._check_config_dict(sys_manager._config)

        self.assertIn('testservice', sys_manager._config['startup_services'])
        self.assertIsNone(sys_manager._config['startup_services']['testservice'])

    def _check_config_dict(self, config):
        """
        check system properties
        """
        self.assertIsInstance(config, emews.base.config.Config)
        self.assertEqual(len(config), 4)

        # check the config_dict for K/Vs common to all testing scenarios
        self.assertIn('general', config)
        self.assertIsInstance(config['general'], emews.base.config.Config)
        self.assertIn('service_start_delay', config['general'])
        self.assertEqual(config['general']['service_start_delay'], 300)
        self.assertIn('thread_shutdown_wait', config['general'])
        self.assertEqual(config['general']['thread_shutdown_wait'], 5)

        self.assertIn('communication', config)
        self.assertIsInstance(config['communication'], emews.base.config.Config)
        self.assertIn('host', config['communication'])
        self.assertEqual(config['communication']['host'], 'localhost')
        self.assertIn('port', config['communication'])
        self.assertEqual(config['communication']['port'], 32518)

        self.assertIn('logging', config)
        self.assertIsInstance(config['logging'], emews.base.config.Config)
        self.assertIn('logger', config['logging'])
        self.assertEqual(config['logging']['logger'], 'emews.testing')
        self.assertIn('message_level', config['logging'])
        self.assertEqual(config['logging']['message_level'], 'DEBUG')

        self.assertIn('startup_services', config)
