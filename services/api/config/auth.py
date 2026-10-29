from .settings import get_settings
from typing import Optional

class AuthConfig:
    """Authentication configuration."""
    
    def __init__(self):
        self.settings = get_settings()
    
    @property
    def jwt_secret(self) -> str:
        return self.settings.JWT_SECRET
    
    @property
    def jwt_algorithm(self) -> str:
        return self.settings.JWT_ALGORITHM
    
    @property
    def jwt_expire_minutes(self) -> int:
        return self.settings.JWT_EXPIRE_MINUTES
    
    @property
    def google_enabled(self) -> bool:
        return self.settings.GOOGLE_CLIENT_ID is not None and self.settings.GOOGLE_CLIENT_SECRET is not None
    
    @property
    def facebook_enabled(self) -> bool:
        return self.settings.FACEBOOK_CLIENT_ID is not None and self.settings.FACEBOOK_CLIENT_SECRET is not None
    
    def get_google_config(self) -> Optional[dict]:
        if self.google_enabled:
            return {
                "client_id": self.settings.GOOGLE_CLIENT_ID,
                "client_secret": self.settings.GOOGLE_CLIENT_SECRET
            }
        return None
    
    def get_facebook_config(self) -> Optional[dict]:
        if self.facebook_enabled:
            return {
                "client_id": self.settings.FACEBOOK_CLIENT_ID,
                "client_secret": self.settings.FACEBOOK_CLIENT_SECRET
            }
        return None
