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

        # returned instance contains specific K/Vs
        self.assertIn('general', config)
        self.assertIn('service_start_delay', config['general'])
        self.assertEqual(config['general']['service_start_delay'], 300)
        self.assertIn('logging', config)
        self.assertIn('message_level', config['logging'])
        self.assertEqual(config['logging']['message_level'], 'DEBUG')
        self.assertIn('startup_services', config)
        self.assertIsNone(config['startup_services'])

        # returned instance has proper len
        self.assertEqual(len(config), 3)

    def test_config(self):
        """[base.config.Config]"""
        config = emews.base.config.Config(
            emews.base.config.parse(os.path.abspath('base/tests/sample_conf.yml')))

        self.assertEqual(len(config), 3)

        # K/Vs are present (and are accessable in both dot and index notation)
        self.assertIn('general', config)
        self.assertIsInstance(config['general'], emews.base.config.Config)
        self.assertIsInstance(config.general, emews.base.config.Config)
        self.assertIn('service_start_delay', config['general'])
        self.assertIn('service_start_delay', config.general)
        self.assertEqual(config['general']['service_start_delay'], 300)
        self.assertEqual(config.general.service_start_delay, 300)
        self.assertIn('logging', config)
        self.assertIsInstance(config['logging'], emews.base.config.Config)
        self.assertIsInstance(config.logging, emews.base.config.Config)
        self.assertIn('logger_parameters', config['logging'])
        self.assertIn('logger_parameters', config.logging)
        self.assertIsInstance(config['logging']['logger_parameters'], emews.base.config.Config)
        self.assertIsInstance(config.logging.logger_parameters, emews.base.config.Config)
        self.assertIsInstance(config['logging'], emews.base.config.Config)
        self.assertIn('host', config['logging']['logger_parameters'])
        self.assertIn('host', config.logging.logger_parameters)
        self.assertEqual(config['logging']['logger_parameters']['host'], '10.0.0.21')
        self.assertEqual(config.logging.logger_parameters.host, '10.0.0.21')
        self.assertIn('port', config['logging']['logger_parameters'])
        self.assertIn('port', config.logging.logger_parameters)
        self.assertEqual(config['logging']['logger_parameters']['port'], 32519)
        self.assertEqual(config.logging.logger_parameters.port, 32519)
