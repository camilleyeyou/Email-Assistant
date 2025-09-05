#!/usr/bin/env python3
"""
Email Assistant Configuration - Simplified Version
"""

import os
import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # ================================
    # CORE APPLICATION SETTINGS
    # ================================
    APP_NAME: str = "Email Assistant"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-powered email processing and management system"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ================================
    # SECURITY SETTINGS
    # ================================
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Security
    API_KEY: Optional[str] = None
    
    # ================================
    # DATABASE SETTINGS
    # ================================
    DATABASE_URL: str = "sqlite:///./email_assistant.db"
    
    # ================================
    # CORS AND FRONTEND SETTINGS
    # ================================
    FRONTEND_URL: str = "http://localhost:3000"
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "https://*.railway.app",
        "https://*.render.com", 
        "https://*.vercel.app",
        "https://*.netlify.app"
    ]
    
    # ================================
    # EMAIL PROCESSING SETTINGS
    # ================================
    EMAIL_BATCH_SIZE: int = 10
    MAX_EMAIL_BATCH_SIZE: int = 50
    
    # Processing timeouts (seconds)
    EMAIL_PROCESSING_TIMEOUT: int = 300
    IMAP_CONNECTION_TIMEOUT: int = 30
    SMTP_CONNECTION_TIMEOUT: int = 30
    
    # Email content limits
    MAX_EMAIL_CONTENT_LENGTH: int = 10000
    MAX_SUBJECT_LENGTH: int = 200
    
    # ================================
    # RATE LIMITING SETTINGS
    # ================================
    RATE_LIMIT_PER_MINUTE: int = 60
    EMAIL_PROCESS_RATE_LIMIT: int = 10
    
    # ================================
    # LOGGING SETTINGS
    # ================================
    LOG_LEVEL: str = "INFO"
    ACCESS_LOG: bool = True
    
    # ================================
    # FEATURE FLAGS
    # ================================
    ENABLE_DOCS: bool = True
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"
    
    ENABLE_EMAIL_PROCESSING: bool = True
    ENABLE_RESPONSE_GENERATION: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_METRICS: bool = False
    
    # ================================
    # EMAIL PROVIDER SETTINGS
    # ================================
    GMAIL_IMAP_SERVER: str = "imap.gmail.com"
    GMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    
    OUTLOOK_IMAP_SERVER: str = "outlook.office365.com"
    OUTLOOK_SMTP_SERVER: str = "smtp-mail.outlook.com"
    
    YAHOO_IMAP_SERVER: str = "imap.mail.yahoo.com"
    YAHOO_SMTP_SERVER: str = "smtp.mail.yahoo.com"
    
    # ================================
    # DEVELOPMENT SETTINGS
    # ================================
    DEV_RELOAD: bool = True
    
    # Security settings for middleware
    TRUSTED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1", 
        "*.railway.app",
        "*.render.com",
        "*.vercel.app"
    ]
    
    # ================================
    # COMPUTED PROPERTIES
    # ================================
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    # ================================
    # CONFIGURATION
    # ================================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# ================================
# SETTINGS INSTANCE
# ================================
def get_settings() -> Settings:
    """Get settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()


# ================================
# HELPER FUNCTIONS
# ================================
def get_cors_config() -> dict:
    """Get CORS configuration"""
    return {
        "allow_origins": settings.ALLOWED_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["*"],
    }


def get_logging_config() -> dict:
    """Get logging configuration"""
    import logging
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    return {
        "level": level,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    }


def validate_production_settings():
    """Validate settings for production deployment"""
    errors = []
    
    if settings.is_production:
        # Check required production settings
        if len(settings.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters in production")
        
        if settings.DEBUG:
            errors.append("DEBUG should be False in production")
        
        if settings.ENABLE_DOCS:
            errors.append("API docs should be disabled in production")
    
    if errors:
        raise ValueError(f"Production validation failed: {'; '.join(errors)}")


# Export settings
__all__ = ["settings", "get_settings", "get_cors_config", "get_logging_config", "validate_production_settings"]