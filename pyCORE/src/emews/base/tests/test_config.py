'''
unit test module

Created on October 17, 2018
@author: Brian Ricks
'''
from unittest import TestCase

import emews.base.config


class ConfigTest(TestCase):
    '''
    Unit tests for config.py
    '''

    def test_parse(self):
        '''
        Unit test for parse() function.
        '''
        # no file given as input
        config = emews.base.config.parse(None)
        TestCase.assertIsNone(config)

        # returned instance is a dict
        config = emews.base.config.parse('sample_conf.yml')
        TestCase.assertIsInstance(config, dict)

        # returned instance contains specific K/Vs
        TestCase.assertIn('general', config)
        TestCase.assertIn('service_start_delay', config['general'])
        TestCase.assertEqual(config['general']['service_start_delay'], 300)
        TestCase.assertIn('logging', config)
        TestCase.assertIn('message_level', config['logging'])
        TestCase.AssertEqual(config['logging']['message_level'], 'DEBUG')
        TestCase.AssertIn('startup_services', config)
        TestCase.assertIsNone(config['startup_services'])

        # returned instance has proper len
        TestCase.assertEqual(len(config), 3)
