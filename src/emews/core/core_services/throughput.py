"""
Throughput CoreService.

Created on Jun 18, 2018
@author: Brian Ricks
"""
import os

from core.service import CoreService


class SiteCrawler(CoreService):
    """CORE Service class for the eMews daemon."""

    name = "Throughput"
    group = "eMews"

    configs = ("emews_throughput.sh",)
    startindex = 50  # make sure this is higher than the emews daemon CoreService
    dirs = ()
    startup = ("sh emews_throughput.sh",)
    shutdown = ()
    validate = ()

    @classmethod
    def generate_config(cls, node, filename):
        """Generate the emews daemon per-node specific config."""
        emews_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
        python_path = os.path.join(emews_root, os.pardir)
        return """\
#!/bin/sh
export PYTHONPATH=""" + python_path + """
python """ + emews_root + """/client/servicelauncher.py Throughput 1>> emews_console.log 2>&1
"""
