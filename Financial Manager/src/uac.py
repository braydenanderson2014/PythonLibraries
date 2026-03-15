import time
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ui')))

from settings import SettingsController
from account import AccountManager
from assets.Logger import Logger
logger = Logger()

class UACManager:
    def __init__(self):
        logger.debug("UACManager", "Initializing UACManager")
        # Store authorization issuance time; expiry is computed using current duration
        # {(username, task): issued_at_timestamp}
        self.tokens = {}
        self.settings = SettingsController()
        self.account_manager = AccountManager()
        logger.info("UACManager", "UACManager initialized")

    def require_uac(self):
        # Reload to reflect any recent changes to settings
        try:
            self.settings.load()
        except Exception:
            pass
        uac_required = bool(self.settings.get('uac_enabled'))
        logger.debug("UACManager", f"UAC required: {uac_required}")
        return uac_required

    def get_duration(self):
        try:
            # Reload settings to reflect runtime changes immediately
            self.settings.load()
            duration = float(self.settings.get('uac_duration_seconds') or 0)
            logger.debug("UACManager", f"UAC duration: {duration} seconds")
            return duration
        except Exception as e:
            logger.warning("UACManager", f"Failed to get duration: {e}")
            return 0.0

    def is_authorized(self, username, task):
        """Return True if user is authorized for task within the current duration window.
        If duration is 0 or negative, tokens expire immediately.
        """
        logger.debug("UACManager", f"Checking authorization for {username} on task {task}")
        if not self.require_uac():
            logger.debug("UACManager", "UAC not required, granting access")
            return True
        key = (username, task)
        issued_at = self.tokens.get(key)
        if issued_at is None:
            logger.warning("UACManager", f"No token found for {username} on task {task}")
            return False
        duration = float(self.get_duration() or 0.0)
        now = time.time()
        valid = duration > 0 and (now - issued_at) <= duration
        if not valid:
            # Revoke expired token
            logger.info("UACManager", f"Token expired for {username} on task {task}")
            self.tokens.pop(key, None)
        else:
            logger.debug("UACManager", f"Authorization valid for {username} on task {task}")
        return valid

    def authorize(self, username, password, task):
        logger.debug("UACManager", f"Authorizing {username} for task {task}")
        if not self.require_uac():
            logger.debug("UACManager", "UAC not required, granting authorization")
            return True
        if self.account_manager.verify_password(username, password):
            self.tokens[(username, task)] = time.time()
            logger.info("UACManager", f"Authorization granted for {username} on task {task}")
            return True
        logger.warning("UACManager", f"Authorization failed for {username} on task {task}")
        return False

    def revoke(self, username, task):
        logger.debug("UACManager", f"Revoking token for {username} on task {task}")
        key = (username, task)
        if key in self.tokens:
            del self.tokens[key]
            logger.info("UACManager", f"Token revoked for {username} on task {task}")
        else:
            logger.warning("UACManager", f"No token to revoke for {username} on task {task}")
