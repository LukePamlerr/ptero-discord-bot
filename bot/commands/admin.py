import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from bot.models import GuildConfig, UserConfig, ServerConfig, encryption_manager
from bot.database import get_db
from sqlalchemy import select, delete, update

class AdminCommands(commands.Cog):
    """Admin-only commands for bot management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    admin = app_commands.Group(name="admin", description="Admin-only bot management commands")
    
    @admin.command(name="status", description="Check bot status and statistics")
    async def admin_status(self, interaction: discord.Interaction):
        """Check bot status and statistics"""
        if not await self.bot.check_permissions(interaction, require_admin=True):
            return
        
        guild_id = str(interaction.guild.id)
        
        async for db in get_db():
            # Get guild config
            guild_result = await db.execute(
                select(GuildConfig).where(GuildConfig.guild_id == guild_id)
            )
            guild_config = guild_result.scalar_one_or_none()
            
            # Get user configs count
            user_count_result = await db.execute(
                select(UserConfig).where(UserConfig.guild_id == guild_id)
            )
            user_configs = user_count_result.scalars().all()
            
            # Get server configs count
            server_count_result = await db.execute(
                select(ServerConfig).where(ServerConfig.guild_id == guild_id)
            )
            server_configs = server_count_result.scalars().all()
            
            embed = discord.Embed(
                title="📊 Bot Status",
                description=f"Status for {interaction.guild.name}",
                color=discord.Color.blue()
            )
            
            # Guild info
            embed.add_field(
                name="🏢 Guild Information",
                value=(
                    f"**Name:** {interaction.guild.name}\n"
                    f"**ID:** {guild_id}\n"
                    f"**Members:** {interaction.guild.member_count}\n"
                    f"**Admin Role:** {f'<@&{guild_config.admin_role_id}>' if guild_config and guild_config.admin_role_id else 'Not set'}"
                ),
                inline=False
            )
            
            # Configuration stats
            embed.add_field(
                name="⚙️ Configuration Statistics",
                value=(
                    f"**Configured Users:** {len(user_configs)}\n"
                    f"**Linked Servers:** {len(server_configs)}\n"
                    f"**Bot Uptime:** {discord.utils.format_dt(interaction.created_at, style='R')}"
                ),
                inline=False
            )
            
            # Bot info
            embed.add_field(
                name="🤖 Bot Information",
                value=(
                    f"**Latency:** {round(self.bot.latency * 1000)}ms\n"
                    f"**Guilds:** {len(self.bot.guilds)}\n"
                    f"**Commands Loaded:** {len(self.bot.tree.get_commands())}"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @admin.command(name="users", description="List all users with configured panels")
    async def admin_users(self, interaction: discord.Interaction):
        """List all users who have configured their panels"""
        if not await self.bot.check_permissions(interaction, require_admin=True):
            return
        
        guild_id = str(interaction.guild.id)
        
        async for db in get_db():
            # Get all user configs for this guild
            user_result = await db.execute(
                select(UserConfig).where(UserConfig.guild_id == guild_id)
            )
            user_configs = user_result.scalars().all()
            
            if not user_configs:
                embed = discord.Embed(
                    title="👥 No Configured Users",
                    description="No users have configured their Pterodactyl panels yet.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="👥 Configured Users",
                description=f"Found {len(user_configs)} user(s) with configured panels",
                color=discord.Color.blue()
            )
            
            for user_config in user_configs:
                try:
                    member = interaction.guild.get_member(int(user_config.discord_user_id))
                    member_name = member.display_name if member else f"User {user_config.discord_user_id}"
                    
                    # Get panel URL (decrypted)
                    panel_url = encryption_manager.decrypt(user_config.panel_url)
                    
                    # Get server count for this user
                    server_result = await db.execute(
                        select(ServerConfig).where(
                            ServerConfig.discord_user_id == user_config.discord_user_id,
                            ServerConfig.guild_id == guild_id
                        )
                    )
                    server_count = len(server_result.scalars().all())
                    
                    field_value = (
                        f"**User:** {member_name}\n"
                        f"**Panel:** {panel_url}\n"
                        f"**Linked Servers:** {server_count}\n"
                        f"**Can Manage Servers:** {'✅' if user_config.can_manage_servers else '❌'}\n"
                        f"**Can Create Users:** {'✅' if user_config.can_create_users else '❌'}\n"
                        f"**Max Servers:** {user_config.max_servers}"
                    )
                    
                    embed.add_field(
                        name=f"👤 {member_name}",
                        value=field_value,
                        inline=False
                    )
                    
                except Exception as e:
                    embed.add_field(
                        name=f"❌ Error loading user {user_config.discord_user_id}",
                        value=f"Error: {str(e)}",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @admin.command(name="audit", description="View audit logs")
    @app_commands.describe(
        limit="Number of recent entries to show (max 50)",
        user_id="Filter by specific user ID (optional)",
        action="Filter by action type (optional)"
    )
    async def admin_audit(self, interaction: discord.Interaction,
                         limit: int = 20, user_id: Optional[str] = None,
                         action: Optional[str] = None):
        """View audit logs"""
        if not await self.bot.check_permissions(interaction, require_admin=True):
            return
        
        if limit > 50:
            limit = 50
        
        guild_id = str(interaction.guild.id)
        
        async for db in get_db():
            from bot.models import AuditLog
            from sqlalchemy import and_, or_, desc
            
            # Build query
            query = select(AuditLog).where(AuditLog.guild_id == guild_id)
            
            if user_id:
                query = query.where(AuditLog.discord_user_id == user_id)
            
            if action:
                query = query.where(AuditLog.action.ilike(f"%{action}%"))
            
            query = query.order_by(desc(AuditLog.timestamp)).limit(limit)
            
            result = await db.execute(query)
            audit_logs = result.scalars().all()
            
            if not audit_logs:
                embed = discord.Embed(
                    title="📋 No Audit Logs Found",
                    description="No audit logs match the specified criteria.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📋 Recent Audit Logs",
                description=f"Showing {len(audit_logs)} most recent entries",
                color=discord.Color.blue()
            )
            
            for log in audit_logs:
                try:
                    member = interaction.guild.get_member(int(log.discord_user_id))
                    member_name = member.display_name if member else f"User {log.discord_user_id}"
                    
                    status_emoji = "✅" if log.success else "❌"
                    
                    field_value = (
                        f"**User:** {member_name}\n"
                        f"**Action:** {log.action}\n"
                        f"**Target:** {log.target_type} {log.target_id or ''}\n"
                        f"**Success:** {status_emoji} {log.success}\n"
                        f"**Time:** {discord.utils.format_dt(log.timestamp, style='R')}"
                    )
                    
                    if log.error_message:
                        field_value += f"\n**Error:** {log.error_message}"
                    
                    if log.details:
                        details_str = ", ".join([f"{k}: {v}" for k, v in log.details.items()])
                        field_value += f"\n**Details:** {details_str}"
                    
                    embed.add_field(
                        name=f"{status_emoji} {log.action.title()}",
                        value=field_value,
                        inline=False
                    )
                    
                except Exception as e:
                    embed.add_field(
                        name="❌ Error loading log entry",
                        value=f"Error: {str(e)}",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @admin.command(name="permissions", description="Manage user permissions")
    @app_commands.describe(
        user="The user to modify permissions for",
        can_manage_servers="Allow user to manage servers",
        can_create_users="Allow user to create users",
        max_servers="Maximum number of servers user can link"
    )
    async def admin_permissions(self, interaction: discord.Interaction,
                               user: discord.Member,
                               can_manage_servers: Optional[bool] = None,
                               can_create_users: Optional[bool] = None,
                               max_servers: Optional[int] = None):
        """Modify user permissions"""
        if not await self.bot.check_permissions(interaction, require_admin=True):
            return
        
        guild_id = str(interaction.guild.id)
        target_user_id = str(user.id)
        
        # Check if at least one permission is being modified
        if all(x is None for x in [can_manage_servers, can_create_users, max_servers]):
            await interaction.response.send_message(
                "❌ Please specify at least one permission to modify.",
                ephemeral=True
            )
            return
        
        async for db in get_db():
            # Get user config
            user_result = await db.execute(
                select(UserConfig).where(
                    UserConfig.discord_user_id == target_user_id,
                    UserConfig.guild_id == guild_id
                )
            )
            user_config = user_result.scalar_one_or_none()
            
            if not user_config:
                await interaction.response.send_message(
                    f"❌ User {user.mention} hasn't configured their Pterodactyl panel yet.",
                    ephemeral=True
                )
                return
            
            # Update permissions
            updated_fields = []
            
            if can_manage_servers is not None:
                user_config.can_manage_servers = can_manage_servers
                updated_fields.append(f"Server Management: {'✅' if can_manage_servers else '❌'}")
            
            if can_create_users is not None:
                user_config.can_create_users = can_create_users
                updated_fields.append(f"User Creation: {'✅' if can_create_users else '❌'}")
            
            if max_servers is not None:
                if max_servers < 0:
                    await interaction.response.send_message(
                        "❌ Max servers cannot be negative.",
                        ephemeral=True
                    )
                    return
                user_config.max_servers = max_servers
                updated_fields.append(f"Max Servers: {max_servers}")
            
            await db.commit()
            
            embed = discord.Embed(
                title="✅ Permissions Updated",
                description=f"Updated permissions for {user.mention}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Updated Permissions",
                value="\n".join(updated_fields),
                inline=False
            )
            
            # Show current permissions
            embed.add_field(
                name="Current Permissions",
                value=(
                    f"**Server Management:** {'✅' if user_config.can_manage_servers else '❌'}\n"
                    f"**User Creation:** {'✅' if user_config.can_create_users else '❌'}\n"
                    f"**Max Servers:** {user_config.max_servers}"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=str(interaction.user.id),
                guild_id=guild_id,
                action="admin_permissions_update",
                target_type="user_config",
                target_id=target_user_id,
                details={
                    "target_user": user.display_name,
                    "updated_fields": updated_fields
                },
                success=True
            )
    
    @admin.command(name="reset", description="Reset a user's configuration")
    @app_commands.describe(
        user="The user to reset configuration for",
        confirm="Type 'RESET' to confirm the reset"
    )
    async def admin_reset(self, interaction: discord.Interaction,
                         user: discord.Member, confirm: str):
        """Reset a user's entire configuration"""
        if not await self.bot.check_permissions(interaction, require_admin=True):
            return
        
        if confirm != "RESET":
            await interaction.response.send_message(
                "❌ You must type 'RESET' to confirm the reset.",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        target_user_id = str(user.id)
        
        async for db in get_db():
            # Get user config
            user_result = await db.execute(
                select(UserConfig).where(
                    UserConfig.discord_user_id == target_user_id,
                    UserConfig.guild_id == guild_id
                )
            )
            user_config = user_result.scalar_one_or_none()
            
            if not user_config:
                await interaction.response.send_message(
                    f"❌ User {user.mention} hasn't configured their Pterodactyl panel yet.",
                    ephemeral=True
                )
                return
            
            # Delete user config (cascade will delete server configs)
            await db.execute(
                delete(UserConfig).where(
                    UserConfig.discord_user_id == target_user_id,
                    UserConfig.guild_id == guild_id
                )
            )
            await db.commit()
            
            embed = discord.Embed(
                title="✅ Configuration Reset",
                description=f"Reset configuration for {user.mention}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="⚠️ Warning",
                value="All of this user's Pterodactyl credentials and linked servers have been removed from the bot. They will need to reconfigure their panel using `/config setup`.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=str(interaction.user.id),
                guild_id=guild_id,
                action="admin_reset_user",
                target_type="user_config",
                target_id=target_user_id,
                details={"target_user": user.display_name},
                success=True
            )
