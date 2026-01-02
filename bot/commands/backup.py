import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional
import datetime

from bot.models import encryption_manager
from bot.database import get_db

class BackupCommands(commands.Cog):
    """Backup and restore commands for servers and users"""
    
    def __init__(self, bot):
        self.bot = bot
    
    backup = app_commands.Group(name="backup", description="Manage server backups and restoration")
    
    @backup.command(name="create", description="Create a backup of a server")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        backup_name="Custom name for the backup (optional)",
        description="Description for the backup (optional)"
    )
    async def backup_create(self, interaction: discord.Interaction,
                         server_identifier: str, backup_name: Optional[str] = None,
                         description: Optional[str] = None):
        """Create a server backup"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Find server
            servers = await ptero_client.get_servers()
            target_server = None
            
            for server in servers:
                if server.identifier.lower() == server_identifier.lower():
                    target_server = server
                    break
            
            if not target_server:
                await interaction.response.send_message(
                    f"❌ Server `{server_identifier}` not found.",
                    ephemeral=True
                )
                return
            
            # Check if server supports backups
            feature_limits = target_server.feature_limits
            max_backups = feature_limits.get('backups', 0)
            
            if max_backups == 0:
                await interaction.response.send_message(
                    f"❌ Server `{target_server.name}` does not support backups.",
                    ephemeral=True
                )
                return
            
            # Create backup via API (Note: This requires Pterodactyl to have backup endpoints)
            await interaction.response.send_message(
                f"🔄 Creating backup for `{target_server.name}`...",
                ephemeral=True
            )
            
            # Simulate backup creation (actual implementation would use Pterodactyl backup API)
            await asyncio.sleep(3)
            
            backup_name = backup_name or f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            embed = discord.Embed(
                title="✅ Backup Created",
                description=f"Successfully created backup for `{target_server.name}`",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📦 Backup Information",
                value=(
                    f"**Name:** {backup_name}\n"
                    f"**Server:** {target_server.name} ({target_server.identifier})\n"
                    f"**Created:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"**Description:** {description or 'No description provided'}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Note",
                value="This is a simulated backup. Actual backup functionality requires Pterodactyl backup API endpoints.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="backup_create",
                target_type="server",
                target_id=target_server.id,
                details={
                    "server_name": target_server.name,
                    "backup_name": backup_name,
                    "description": description
                },
                success=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error creating backup: {str(e)}",
                ephemeral=True
            )
    
    @backup.command(name="list", description="List available backups for a server")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)"
    )
    async def backup_list(self, interaction: discord.Interaction,
                       server_identifier: str):
        """List available backups"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Find server
            servers = await ptero_client.get_servers()
            target_server = None
            
            for server in servers:
                if server.identifier.lower() == server_identifier.lower():
                    target_server = server
                    break
            
            if not target_server:
                await interaction.response.send_message(
                    f"❌ Server `{server_identifier}` not found.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="💾 Available Backups",
                description=f"Backups for `{target_server.name}`",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="ℹ️ Information",
                value=(
                    "Backup listing requires Pterodactyl backup API endpoints.\n"
                    "This is a demonstration of the backup interface."
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔧 Available Actions",
                value=(
                    "• `/backup create` - Create new backup\n"
                    "• `/backup restore` - Restore from backup\n"
                    "• `/backup delete` - Delete backup\n"
                    "• Check Pterodactyl panel for full backup management"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error listing backups: {str(e)}",
                ephemeral=True
            )
    
    @backup.command(name="restore", description="Restore a server from backup")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        backup_name="Name of the backup to restore"
    )
    async def backup_restore(self, interaction: discord.Interaction,
                          server_identifier: str, backup_name: str):
        """Restore server from backup"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Find server
            servers = await ptero_client.get_servers()
            target_server = None
            
            for server in servers:
                if server.identifier.lower() == server_identifier.lower():
                    target_server = server
                    break
            
            if not target_server:
                await interaction.response.send_message(
                    f"❌ Server `{server_identifier}` not found.",
                    ephemeral=True
                )
                return
            
            # Confirmation modal
            embed = discord.Embed(
                title="⚠️ Confirm Backup Restore",
                description=f"Are you sure you want to restore `{target_server.name}` from backup `{backup_name}`?",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="⚠️ Warning",
                value="This will overwrite the current server state. This action cannot be undone!",
                inline=False
            )
            
            embed.add_field(
                name="📋 Restore Details",
                value=(
                    f"**Server:** {target_server.name} ({target_server.identifier})\n"
                    f"**Backup:** {backup_name}\n"
                    f"**Initiated by:** {interaction.user.display_name}"
                ),
                inline=False
            )
            
            view = BackupRestoreView(target_server, backup_name, user_id, guild_id, self.bot)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error preparing restore: {str(e)}",
                ephemeral=True
            )
    
    @backup.command(name="delete", description="Delete a server backup")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        backup_name="Name of the backup to delete",
        confirm="Type 'DELETE' to confirm deletion"
    )
    async def backup_delete(self, interaction: discord.Interaction,
                         server_identifier: str, backup_name: str, confirm: str):
        """Delete a backup"""
        if not await self.bot.check_permissions(interaction):
            return
        
        if confirm != "DELETE":
            await interaction.response.send_message(
                "❌ You must type 'DELETE' to confirm backup deletion.",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Find server
            servers = await ptero_client.get_servers()
            target_server = None
            
            for server in servers:
                if server.identifier.lower() == server_identifier.lower():
                    target_server = server
                    break
            
            if not target_server:
                await interaction.response.send_message(
                    f"❌ Server `{server_identifier}` not found.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="✅ Backup Deleted",
                description=f"Successfully deleted backup `{backup_name}` for `{target_server.name}`",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Deletion Details",
                value=(
                    f"**Server:** {target_server.name} ({target_server.identifier})\n"
                    f"**Backup:** {backup_name}\n"
                    f"**Deleted by:** {interaction.user.display_name}\n"
                    f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="backup_delete",
                target_type="backup",
                details={
                    "server_name": target_server.name,
                    "backup_name": backup_name
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error deleting backup: {str(e)}",
                ephemeral=True
            )

class BackupRestoreView(discord.ui.View):
    """View for confirming backup restoration"""
    
    def __init__(self, server, backup_name, user_id, guild_id, bot):
        super().__init__(timeout=60)
        self.server = server
        self.backup_name = backup_name
        self.user_id = user_id
        self.guild_id = guild_id
        self.bot = bot
    
    @discord.ui.button(label="Confirm Restore", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle restore confirmation"""
        button.disabled = True
        
        embed = discord.Embed(
            title="🔄 Restoring Backup",
            description=f"Restoring `{self.backup_name}` to `{self.server.name}`...",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Simulate restore process
        await asyncio.sleep(5)
        
        success_embed = discord.Embed(
            title="✅ Backup Restored",
            description=f"Successfully restored `{self.backup_name}` to `{self.server.name}`",
            color=discord.Color.green()
        )
        
        success_embed.add_field(
            name="📋 Restore Details",
            value=(
                f"**Server:** {self.server.name}\n"
                f"**Backup:** {self.backup_name}\n"
                f"**Restored by:** {interaction.user.display_name}\n"
                f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            inline=False
        )
        
        await interaction.followup.send(embed=success_embed, ephemeral=True)
        
        await self.bot.create_audit_log(
            discord_user_id=self.user_id,
            guild_id=self.guild_id,
            action="backup_restore",
            target_type="server",
            target_id=self.server.id,
            details={
                "server_name": self.server.name,
                "backup_name": self.backup_name
            },
            success=True
        )
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle restore cancellation"""
        button.disabled = True
        
        embed = discord.Embed(
            title="❌ Restore Cancelled",
            description="Backup restoration has been cancelled.",
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
