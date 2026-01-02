import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional

from bot.models import GuildConfig, UserConfig, encryption_manager
from bot.database import get_db

class SetupCommands(commands.Cog):
    """Setup and configuration commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="setup", description="Setup the bot for your server")
    @app_commands.describe(
        admin_role="Role that can manage the bot (optional, defaults to Server Admin)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, 
                   admin_role: Optional[discord.Role] = None):
        """Setup the bot for the server"""
        guild_id = str(interaction.guild.id)
        
        async for db in get_db():
            # Check if already configured
            from sqlalchemy import select
            existing = await db.execute(
                select(GuildConfig).where(GuildConfig.guild_id == guild_id)
            )
            if existing.scalar_one_or_none():
                await interaction.response.send_message(
                    "This server is already configured. Use `/config update` to change settings.",
                    ephemeral=True
                )
                return
            
            # Create new guild config
            guild_config = GuildConfig(
                guild_id=guild_id,
                admin_role_id=str(admin_role.id) if admin_role else None
            )
            db.add(guild_config)
            await db.commit()
            
            await self.bot.create_audit_log(
                discord_user_id=str(interaction.user.id),
                guild_id=guild_id,
                action="setup",
                target_type="guild",
                details={"admin_role_id": guild_config.admin_role_id},
                success=True
            )
            
            embed = discord.Embed(
                title="✅ Bot Setup Complete",
                description="The Pterodactyl bot has been configured for your server!",
                color=discord.Color.green()
            )
            
            if admin_role:
                embed.add_field(
                    name="Admin Role",
                    value=f"{admin_role.mention}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Admin Role",
                    value="Server administrators (users with Administrator permission)",
                    inline=False
                )
            
            embed.add_field(
                name="Next Steps",
                value="1. Use `/config setup` to configure your Pterodactyl panel\n2. Use `/server list` to view your servers",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

class ConfigCommands(commands.Cog):
    """User configuration commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    config = app_commands.Group(name="config", description="Configure your Pterodactyl panel")
    
    @config.command(name="setup", description="Configure your Pterodactyl panel credentials")
    @app_commands.describe(
        panel_url="Your Pterodactyl panel URL (e.g., https://panel.example.com)",
        api_key="Your Pterodactyl Application API Key"
    )
    async def config_setup(self, interaction: discord.Interaction, 
                          panel_url: str, api_key: str):
        """Setup user's Pterodactyl configuration"""
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Validate URL format
        if not panel_url.startswith(('http://', 'https://')):
            await interaction.response.send_message(
                "Panel URL must start with http:// or https://",
                ephemeral=True
            )
            return
        
        # Test API connection
        from bot.pterodactyl import PterodactylAPI
        try:
            ptero_client = PterodactylAPI(panel_url, api_key)
            is_valid = await ptero_client.test_connection()
            
            if not is_valid:
                await interaction.response.send_message(
                    "❌ Failed to connect to your Pterodactyl panel. Please check your URL and API key.",
                    ephemeral=True
                )
                return
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error connecting to panel: {str(e)}",
                ephemeral=True
            )
            return
        
        async for db in get_db():
            from sqlalchemy import select
            
            # Check if user already has config
            existing = await db.execute(
                select(UserConfig).where(
                    UserConfig.discord_user_id == user_id,
                    UserConfig.guild_id == guild_id
                )
            )
            existing_config = existing.scalar_one_or_none()
            
            # Encrypt sensitive data
            encrypted_url = encryption_manager.encrypt(panel_url)
            encrypted_key = encryption_manager.encrypt(api_key)
            
            if existing_config:
                # Update existing config
                existing_config.panel_url = encrypted_url
                existing_config.api_key = encrypted_key
                await db.commit()
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="config_update",
                    target_type="user_config",
                    success=True
                )
                
                await interaction.response.send_message(
                    "✅ Your Pterodactyl configuration has been updated!",
                    ephemeral=True
                )
            else:
                # Create new config
                user_config = UserConfig(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    panel_url=encrypted_url,
                    api_key=encrypted_key
                )
                db.add(user_config)
                await db.commit()
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="config_create",
                    target_type="user_config",
                    success=True
                )
                
                await interaction.response.send_message(
                    "✅ Your Pterodactyl configuration has been saved!\n\n"
                    "You can now use server management commands.",
                    ephemeral=True
                )
    
    @config.command(name="status", description="Check your configuration status")
    async def config_status(self, interaction: discord.Interaction):
        """Check user's configuration status"""
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        async for db in get_db():
            from sqlalchemy import select
            
            # Get user config
            user_result = await db.execute(
                select(UserConfig).where(
                    UserConfig.discord_user_id == user_id,
                    UserConfig.guild_id == guild_id
                )
            )
            user_config = user_result.scalar_one_or_none()
            
            if not user_config:
                embed = discord.Embed(
                    title="❌ Not Configured",
                    description="You haven't configured your Pterodactyl panel yet.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Setup Command",
                    value="Use `/config setup` to configure your panel.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Test connection
            try:
                ptero_client = self.bot.get_ptero_client(user_config)
                is_connected = await ptero_client.test_connection()
                
                status_color = discord.Color.green() if is_connected else discord.Color.red()
                status_emoji = "✅" if is_connected else "❌"
                status_text = "Connected" if is_connected else "Failed to connect"
                
                # Get server count
                servers = await ptero_client.get_servers() if is_connected else []
                
                embed = discord.Embed(
                    title=f"{status_emoji} Configuration Status",
                    color=status_color
                )
                
                embed.add_field(
                    name="Panel Connection",
                    value=status_text,
                    inline=True
                )
                
                if is_connected:
                    embed.add_field(
                        name="Accessible Servers",
                        value=str(len(servers)),
                        inline=True
                    )
                    
                    panel_url = encryption_manager.decrypt(user_config.panel_url)
                    embed.add_field(
                        name="Panel URL",
                        value=panel_url,
                        inline=False
                    )
                
                embed.add_field(
                    name="Permissions",
                    value=f"Can manage servers: {'✅' if user_config.can_manage_servers else '❌'}\n"
                          f"Can create users: {'✅' if user_config.can_create_users else '❌'}\n"
                          f"Max servers: {user_config.max_servers}",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                embed = discord.Embed(
                    title="❌ Configuration Error",
                    description=f"Error testing connection: {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @config.command(name="remove", description="Remove your Pterodactyl configuration")
    async def config_remove(self, interaction: discord.Interaction):
        """Remove user's configuration"""
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        async for db in get_db():
            from sqlalchemy import delete
            
            # Delete user config (cascade will delete server configs)
            await db.execute(
                delete(UserConfig).where(
                    UserConfig.discord_user_id == user_id,
                    UserConfig.guild_id == guild_id
                )
            )
            await db.commit()
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="config_remove",
                target_type="user_config",
                success=True
            )
            
            await interaction.response.send_message(
                "✅ Your Pterodactyl configuration has been removed.",
                ephemeral=True
            )
