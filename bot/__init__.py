"""
Pterodactyl Discord Bot Package

A comprehensive Discord bot for managing Pterodactyl game server panels.
This package provides server management, user administration, and
secure credential storage with full audit logging.

Features:
- Server power management (start/stop/restart/kill)
- Console command execution
- User creation and management
- Encrypted credential storage
- Role-based permissions
- Comprehensive audit logging
- Real-time resource monitoring
"""

__version__ = "1.0.0"
__author__ = "Pterodactyl Discord Bot Team"
__description__ = "Advanced Discord bot for Pterodactyl panel management"

# Import key components for easy access
from bot.core import PteroBot
from bot.models import (
    GuildConfig, 
    UserConfig, 
    ServerConfig, 
    AuditLog,
    encryption_manager
)
from bot.pterodactyl import (
    PterodactylAPI,
    ServerInfo,
    UserInfo,
    ServerState
)

__all__ = [
    "PteroBot",
    "GuildConfig",
    "UserConfig", 
    "ServerConfig",
    "AuditLog",
    "encryption_manager",
    "PterodactylAPI",
    "ServerInfo",
    "UserInfo",
    "ServerState",
]

# Package metadata
PACKAGE_INFO = {
    "name": "ptero-discord-bot",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "python_requires": ">=3.8",
    "dependencies": [
        "discord.py>=2.3.2",
        "aiohttp>=3.9.1",
        "sqlalchemy>=2.0.23",
        "alembic>=1.13.1",
        "python-dotenv>=1.0.0",
        "cryptography>=41.0.8",
        "asyncpg>=0.29.0",
        "pydantic>=2.5.2",
    ]
}

# Configuration constants
DEFAULT_CONFIG = {
    "max_servers_per_user": 10,
    "default_permissions": {
        "can_manage_servers": True,
        "can_create_users": False,
    },
    "audit_log_retention_days": 90,
    "encryption_algorithm": "Fernet",
    "api_timeout": 30,
    "max_retries": 3,
}

# Error codes for better error handling
ERROR_CODES = {
    "INVALID_CREDENTIALS": 1001,
    "API_CONNECTION_FAILED": 1002,
    "INSUFFICIENT_PERMISSIONS": 1003,
    "SERVER_NOT_FOUND": 1004,
    "USER_NOT_FOUND": 1005,
    "DATABASE_ERROR": 1006,
    "ENCRYPTION_ERROR": 1007,
    "RATE_LIMIT_EXCEEDED": 1008,
}

# Supported Pterodactyl API versions
SUPPORTED_API_VERSIONS = ["v1"]

# Bot status messages
STATUS_MESSAGES = {
    "starting": "🔄 Initializing Pterodactyl connection...",
    "ready": "✅ Pterodactyl Discord Bot is ready!",
    "error": "❌ Error connecting to Pterodactyl panel",
    "maintenance": "🔧 Bot is under maintenance",
}

# Command categories for help system
COMMAND_CATEGORIES = {
    "setup": {
        "name": "Setup & Configuration",
        "description": "Initial bot setup and user configuration",
        "emoji": "⚙️",
    },
    "server": {
        "name": "Server Management", 
        "description": "Control and monitor your game servers",
        "emoji": "🖥️",
    },
    "user": {
        "name": "User Management",
        "description": "Create and manage Pterodactyl users",
        "emoji": "👥",
    },
    "admin": {
        "name": "Administration",
        "description": "Bot administration and management",
        "emoji": "🛡️",
    },
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "ptero_bot.log",
            "formatter": "detailed",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "discord": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
