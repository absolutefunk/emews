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
        # test if no file given as input
        config = emews.base.config.parse(None)
        TestCase.assertIsNone(config)

        # test that returned instance is a dict
        config = emews.base.config.parse('sample_conf.yml')
        TestCase.assertIsInstance(config, dict)
