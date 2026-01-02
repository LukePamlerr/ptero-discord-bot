import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os
from typing import Optional
import logging

from bot.database import init_db, get_db
from bot.models import GuildConfig, UserConfig, ServerConfig, AuditLog, encryption_manager
from bot.commands.setup import SetupCommands
from bot.commands.server import ServerCommands
from bot.commands.user import UserCommands
from bot.commands.admin import AdminCommands
from bot.commands.monitoring import MonitoringCommands
from bot.commands.backup import BackupCommands
from bot.commands.schedule import ScheduleCommands, AutomationCommands
from bot.commands.notifications import NotificationCommands, AlertCommands
from bot.commands.analytics import AnalyticsCommands
from bot.commands.utilities import UtilityCommands

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PteroBot(commands.Bot):
    """Main Pterodactyl Discord Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.tree = app_commands.CommandTree(self)
        
    async def setup_hook(self):
        """Setup bot when ready"""
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Add command groups
        await self.add_cog(SetupCommands(self))
        await self.add_cog(ServerCommands(self))
        await self.add_cog(UserCommands(self))
        await self.add_cog(AdminCommands(self))
        await self.add_cog(MonitoringCommands(self))
        await self.add_cog(BackupCommands(self))
        await self.add_cog(ScheduleCommands(self))
        await self.add_cog(AutomationCommands(self))
        await self.add_cog(NotificationCommands(self))
        await self.add_cog(AlertCommands(self))
        await self.add_cog(AnalyticsCommands(self))
        await self.add_cog(UtilityCommands(self))
        
        # Sync commands globally or to specific guild
        guild_id = os.getenv('DISCORD_GUILD_ID')
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"Commands synced to guild {guild_id}")
        else:
            await self.tree.sync()
            logger.info("Commands synced globally")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot logged in as {self.user}")
        logger.info(f"Bot in {len(self.guilds)} guilds")
        
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Pterodactyl servers"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild: discord.Guild):
        """Called when bot joins a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Create guild config in database
        async for db in get_db():
            guild_config = GuildConfig(guild_id=str(guild.id))
            db.add(guild_config)
            await db.commit()
            break
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when bot leaves a guild"""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        
        # Clean up database (cascade will handle related records)
        async for db in get_db():
            from sqlalchemy import delete
            await db.execute(
                delete(GuildConfig).where(GuildConfig.guild_id == str(guild.id))
            )
            await db.commit()
            break
    
    async def get_user_config(self, discord_user_id: str, guild_id: str) -> Optional[UserConfig]:
        """Get user configuration from database"""
        async for db in get_db():
            from sqlalchemy import select
            result = await db.execute(
                select(UserConfig).where(
                    UserConfig.discord_user_id == discord_user_id,
                    UserConfig.guild_id == guild_id
                )
            )
            return result.scalar_one_or_none()
    
    async def create_audit_log(self, discord_user_id: str, guild_id: str, 
                              action: str, target_type: str, target_id: str = None,
                              details: dict = None, success: bool = True, 
                              error_message: str = None):
        """Create an audit log entry"""
        async for db in get_db():
            audit_log = AuditLog(
                discord_user_id=discord_user_id,
                guild_id=guild_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
                success=success,
                error_message=error_message
            )
            db.add(audit_log)
            await db.commit()
            break
    
    def get_ptero_client(self, user_config: UserConfig):
        """Get Pterodactyl API client for user"""
        from bot.pterodactyl import PterodactylAPI
        
        panel_url = encryption_manager.decrypt(user_config.panel_url)
        api_key = encryption_manager.decrypt(user_config.api_key)
        
        return PterodactylAPI(panel_url, api_key)
    
    async def check_permissions(self, interaction: discord.Interaction, 
                               require_admin: bool = False) -> bool:
        """Check if user has required permissions"""
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Get guild config
        async for db in get_db():
            from sqlalchemy import select
            guild_result = await db.execute(
                select(GuildConfig).where(GuildConfig.guild_id == guild_id)
            )
            guild_config = guild_result.scalar_one_or_none()
            
            if not guild_config:
                await interaction.response.send_message(
                    "Guild not configured. Please run `/setup` first.",
                    ephemeral=True
                )
                return False
            
            # Check if user is admin
            if require_admin:
                if guild_config.admin_role_id:
                    member = interaction.guild.get_member(int(user_id))
                    if not any(role.id == int(guild_config.admin_role_id) for role in member.roles):
                        await interaction.response.send_message(
                            "You need admin permissions to use this command.",
                            ephemeral=True
                        )
                        return False
                elif not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message(
                        "You need administrator permissions to use this command.",
                        ephemeral=True
                    )
                    return False
            
            # Check if user has configured their Pterodactyl credentials
            user_config = await self.get_user_config(user_id, guild_id)
            if not user_config:
                await interaction.response.send_message(
                    "You need to configure your Pterodactyl credentials first. Use `/config setup`.",
                    ephemeral=True
                )
                return False
            
            return True
        
        return False
