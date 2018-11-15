"""
Unit test module - config.py.

Created on October 17, 2018
@author: Brian Ricks
"""
import os
from unittest import TestCase

import emews.base.config


class ConfigTest(TestCase):
    """Unit tests for config.py."""

    def test_parse(self):
        """[base.config.parse()]"""
        # no file given as input
        config = emews.base.config.parse(None)
        self.assertIsNone(config)

        # returned instance is a dict
        config = emews.base.config.parse(os.path.abspath('base/tests/sample_conf.yml'))
        self.assertIsInstance(config, dict)

        # returned instance has proper len
        self.assertEqual(len(config), 4)

        # returned instance contains specific K/Vs
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
        self.assertIsNone(config['startup_services'])

    def test_config(self):
        """[base.config.Config]"""
        config = emews.base.config.Config(
            emews.base.config.parse(os.path.abspath('base/tests/sample_conf.yml')))

        self.assertEqual(len(config), 4)

        # K/Vs are present (and are accessable in both dot and index notation)
        self.assertIn('general', config)
        self.assertIsInstance(config['general'], emews.base.config.Config)
        self.assertIsInstance(config.general, emews.base.config.Config)
        self.assertIn('service_start_delay', config['general'])
        self.assertIn('service_start_delay', config.general)
        self.assertEqual(config['general']['service_start_delay'], 300)
        self.assertEqual(config.general.service_start_delay, 300)
        self.assertIn('thread_shutdown_wait', config['general'])
        self.assertIn('thread_shutdown_wait', config.general)
        self.assertEqual(config['general']['thread_shutdown_wait'], 5)
        self.assertEqual(config.general.thread_shutdown_wait, 5)

        self.assertIn('communication', config)
        self.assertIsInstance(config['communication'], emews.base.config.Config)
        self.assertIsInstance(config.communication, emews.base.config.Config)
        self.assertIn('host', config['communication'])
        self.assertEqual(config['communication']['host'], 'localhost')
        self.assertEqual(config.communication.host, 'localhost')
        self.assertIn('port', config['communication'])
        self.assertEqual(config['communication']['port'], 32518)
        self.assertEqual(config.communication.port, 32518)

        self.assertIn('logging', config)
        self.assertIsInstance(config['logging'], emews.base.config.Config)
        self.assertIsInstance(config.logging, emews.base.config.Config)
        self.assertIn('logger', config['logging'])
        self.assertEqual(config['logging']['logger'], 'emews.testing')
        self.assertEqual(config.logging.logger, 'emews.testing')
        self.assertIn('message_level', config['logging'])
        self.assertEqual(config['logging']['message_level'], 'DEBUG')
        self.assertEqual(config.logging.message_level, 'DEBUG')

        self.assertIn('startup_services', config)
        self.assertIsNone(config['startup_services'])
        self.assertIsNone(config.startup_services)
