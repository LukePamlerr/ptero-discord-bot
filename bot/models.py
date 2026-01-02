from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import os

Base = declarative_base()

class GuildConfig(Base):
    """Guild-specific configuration"""
    __tablename__ = 'guild_configs'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String(20), unique=True, nullable=False)
    admin_role_id = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("UserConfig", back_populates="guild", cascade="all, delete-orphan")
    servers = relationship("ServerConfig", back_populates="guild", cascade="all, delete-orphan")

class UserConfig(Base):
    """User configuration for Pterodactyl panels"""
    __tablename__ = 'user_configs'
    
    id = Column(Integer, primary_key=True)
    discord_user_id = Column(String(20), nullable=False)
    guild_id = Column(String(20), ForeignKey('guild_configs.guild_id'), nullable=False)
    
    # Encrypted Pterodactyl credentials
    panel_url = Column(Text, nullable=False)
    api_key = Column(Text, nullable=False)
    
    # User permissions
    can_create_users = Column(Boolean, default=False)
    can_manage_servers = Column(Boolean, default=True)
    max_servers = Column(Integer, default=10)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    guild = relationship("GuildConfig", back_populates="users")
    servers = relationship("ServerConfig", back_populates="user", cascade="all, delete-orphan")

class ServerConfig(Base):
    """Server configurations linked to users"""
    __tablename__ = 'server_configs'
    
    id = Column(Integer, primary_key=True)
    discord_user_id = Column(String(20), nullable=False)
    guild_id = Column(String(20), ForeignKey('guild_configs.guild_id'), nullable=False)
    user_config_id = Column(Integer, ForeignKey('user_configs.id'), nullable=False)
    
    # Pterodactyl server info
    ptero_server_id = Column(String(50), nullable=False)
    server_name = Column(String(100), nullable=False)
    server_identifier = Column(String(100), nullable=False)
    
    # Server settings
    auto_start = Column(Boolean, default=False)
    notification_channel_id = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    guild = relationship("GuildConfig", back_populates="servers")
    user = relationship("UserConfig", back_populates="servers")

class AuditLog(Base):
    """Audit log for all actions"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    discord_user_id = Column(String(20), nullable=False)
    guild_id = Column(String(20), nullable=False)
    action = Column(String(50), nullable=False)
    target_type = Column(String(20), nullable=False)  # 'server', 'user', 'config'
    target_id = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class EncryptionManager:
    """Handles encryption/decryption of sensitive data"""
    
    def __init__(self):
        # Generate a key from the database URL for simplicity
        # In production, you might want to use a proper secret management system
        import os
        import hashlib
        from cryptography.fernet import Fernet
        
        db_url = os.getenv('DATABASE_URL', 'default_key_for_encryption')
        # Create a consistent 32-byte key from the database URL
        key_bytes = hashlib.sha256(db_url.encode()).digest()
        self.key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Global encryption manager
encryption_manager = EncryptionManager()
