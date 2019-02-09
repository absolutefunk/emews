"""
Test dummy service.

Created on Jan 19, 2018
@author: Brian Ricks
"""
import emews.services.baseservice


class TestService(emews.services.baseservice.BaseService):
    """Classdocs."""

    def run_service(self):
        """@Override Test service start entry."""
        self.logger.info("Test Service Started.")
