"""
CoreServices: classes which interface with the CORE network emulator.

This is the main CoreService for the eMews daemon.  Must be launched on a node before any clients.

Created on Mar 5, 2018
@author: Brian Ricks
"""
import os

from core.service import CoreService


class EmewsDaemon(CoreService):
    """CORE Service class for the eMews daemon."""

    name = "eMewsDaemon"
    group = "eMews"

    configs = ("runemewsdaemon.sh", "emews_node.yml",)
    startindex = 20
    dirs = ()
    startup = ("sh runemewsdaemon.sh",)
    shutdown = ()
    validate = ()

    @classmethod
    def generate_config(cls, node, filename):
        """Generate the emews daemon per-node specific config."""
        emews_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
        python_path = os.path.join(emews_root, os.pardir)
        if filename == "runemewsdaemon.sh":
            return """\
#!/bin/sh
export PYTHONPATH=""" + python_path + """
python """ + emews_root + """/emewsdaemon.py -c emews_node.yml 1>> emews_console.log 2>&1
"""
        elif filename == "emews_node.yml":
            return """\
# Generated by the eMews daemon CORE service
# YAML 1.2 compliant
general:
  # Name of the node
  node_name: %s
""" % (node.name)

        return ""
