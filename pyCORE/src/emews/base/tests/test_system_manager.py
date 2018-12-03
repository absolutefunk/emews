"""
Unit test module - system_manager.py.

Created on October 17, 2018
@author: Brian Ricks
"""
from unittest import TestCase

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
            'sys_config': 'base/tests/sample_conf.yml',
            'node_config': None,
            'node_name': 'TestNode',
            'local': False
        })

        # local mode
        self.args2 = emews.base.config.Config({
            'sys_config': 'base/tests/sample_conf.yml',
            'node_config': None,
            'node_name': 'TestNode',
            'local': True
        })

    def test_system_init(self):
        """
        Unit test for system_init() function
        """
        # 1 ##
        # using self.args for the args
        sys_manager = emews.base.system_init.system_init(self.args)

        self.assertIsInstance(sys_manager, emews.base.system_manager.SystemManager)
        self.assertEqual(sys_manager._local_mode, False)

        # 2 ##
        # using self.args2 for the args (local mode)
        sys_manager = emews.base.system_init.system_init(self.args2)

        self.assertIsInstance(sys_manager, emews.base.system_manager.SystemManager)
        self.assertEqual(sys_manager._local_mode, True)
