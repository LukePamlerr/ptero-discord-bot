import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional

from bot.models import ServerConfig, encryption_manager
from bot.database import get_db
from bot.pterodactyl import ServerState

class ServerCommands(commands.Cog):
    """Server management commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    server = app_commands.Group(name="server", description="Manage your Pterodactyl servers")
    
    @server.command(name="list", description="List all your servers")
    async def server_list(self, interaction: discord.Interaction):
        """List all servers for the user"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Get user config
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            await interaction.response.send_message(
                "You need to configure your Pterodactyl panel first. Use `/config setup`.",
                ephemeral=True
            )
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            servers = await ptero_client.get_servers(include_relations=True)
            
            if not servers:
                embed = discord.Embed(
                    title="🖥️ No Servers Found",
                    description="You don't have any servers on your Pterodactyl panel.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🖥️ Your Servers",
                description=f"Found {len(servers)} server(s) on your panel",
                color=discord.Color.blue()
            )
            
            for server in servers[:10]:  # Limit to 10 servers to avoid embed limits
                status_emoji = self.get_status_emoji(server.state)
                status_color = self.get_status_color(server.state)
                
                field_value = (
                    f"**ID:** `{server.identifier}`\n"
                    f"**Status:** {status_emoji} {server.state.value.title()}\n"
                    f"**Memory:** {server.limits.get('memory', 'N/A')} MB\n"
                    f"**CPU:** {server.limits.get('cpu', 'N/A')}%\n"
                    f"**Disk:** {server.limits.get('disk', 'N/A')} MB"
                )
                
                embed.add_field(
                    name=f"{server.name}",
                    value=field_value,
                    inline=False
                )
            
            if len(servers) > 10:
                embed.set_footer(text=f"Showing 10 of {len(servers)} servers")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error fetching servers: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="server_list",
                target_type="server",
                success=False,
                error_message=str(e)
            )
    
    @server.command(name="info", description="Get detailed information about a server")
    @app_commands.describe(server_identifier="Server identifier (e.g., mc123)")
    async def server_info(self, interaction: discord.Interaction, server_identifier: str):
        """Get detailed server information"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Find server by identifier
            servers = await ptero_client.get_servers()
            target_server = None
            
            for server in servers:
                if server.identifier.lower() == server_identifier.lower():
                    target_server = server
                    break
            
            if not target_server:
                await interaction.response.send_message(
                    f"❌ Server with identifier `{server_identifier}` not found.",
                    ephemeral=True
                )
                return
            
            # Get detailed server info
            detailed_server = await ptero_client.get_server(target_server.id)
            resources = await ptero_client.get_server_resources(target_server.id)
            
            embed = discord.Embed(
                title=f"🖥️ {detailed_server.name}",
                description=f"**Identifier:** `{detailed_server.identifier}`",
                color=self.get_status_color(detailed_server.state)
            )
            
            # Status
            status_emoji = self.get_status_emoji(detailed_server.state)
            embed.add_field(
                name="📊 Status",
                value=f"{status_emoji} {detailed_server.state.value.title()}",
                inline=True
            )
            
            # Resource Usage
            if resources:
                resource_state = resources.get("state", {})
                embed.add_field(
                    name="💾 Resource Usage",
                    value=(
                        f"**CPU:** {resource_state.get('cpu_absolute', 0):.1f}%\n"
                        f"**Memory:** {resource_state.get('memory_bytes', 0) / 1024 / 1024:.1f} MB\n"
                        f"**Disk:** {resource_state.get('disk_bytes', 0) / 1024 / 1024:.1f} MB"
                    ),
                    inline=True
                )
            
            # Limits
            limits = detailed_server.limits
            embed.add_field(
                name="⚙️ Limits",
                value=(
                    f"**Memory:** {limits.get('memory', 'N/A')} MB\n"
                    f"**CPU:** {limits.get('cpu', 'N/A')}%\n"
                    f"**Disk:** {limits.get('disk', 'N/A')} MB"
                ),
                inline=True
            )
            
            # Allocation info
            if detailed_server.allocation:
                alloc = detailed_server.allocation
                embed.add_field(
                    name="🌐 Network",
                    value=(
                        f"**IP:** {alloc.get('ip', 'N/A')}\n"
                        f"**Port:** {alloc.get('port', 'N/A')}"
                    ),
                    inline=True
                )
            
            # Feature limits
            feature_limits = detailed_server.feature_limits
            embed.add_field(
                name="🔧 Features",
                value=(
                    f"**Backups:** {feature_limits.get('backups', 'N/A')}\n"
                    f"**Databases:** {feature_limits.get('databases', 'N/A')}\n"
                    f"**Allocations:** {feature_limits.get('allocations', 'N/A')}"
                ),
                inline=True
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="server_info",
                target_type="server",
                target_id=detailed_server.id,
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error fetching server info: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="server_info",
                target_type="server",
                target_id=server_identifier,
                success=False,
                error_message=str(e)
            )
    
    @server.command(name="start", description="Start a server")
    @app_commands.describe(server_identifier="Server identifier (e.g., mc123)")
    async def server_start(self, interaction: discord.Interaction, server_identifier: str):
        """Start a server"""
        await self.server_power_action(interaction, server_identifier, "start")
    
    @server.command(name="stop", description="Stop a server")
    @app_commands.describe(server_identifier="Server identifier (e.g., mc123)")
    async def server_stop(self, interaction: discord.Interaction, server_identifier: str):
        """Stop a server"""
        await self.server_power_action(interaction, server_identifier, "stop")
    
    @server.command(name="restart", description="Restart a server")
    @app_commands.describe(server_identifier="Server identifier (e.g., mc123)")
    async def server_restart(self, interaction: discord.Interaction, server_identifier: str):
        """Restart a server"""
        await self.server_power_action(interaction, server_identifier, "restart")
    
    @server.command(name="kill", description="Force kill a server")
    @app_commands.describe(server_identifier="Server identifier (e.g., mc123)")
    async def server_kill(self, interaction: discord.Interaction, server_identifier: str):
        """Force kill a server"""
        await self.server_power_action(interaction, server_identifier, "kill")
    
    async def server_power_action(self, interaction: discord.Interaction, 
                                 server_identifier: str, action: str):
        """Handle server power actions"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        if not user_config.can_manage_servers:
            await interaction.response.send_message(
                "You don't have permission to manage servers.",
                ephemeral=True
            )
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
                    f"❌ Server with identifier `{server_identifier}` not found.",
                    ephemeral=True
                )
                return
            
            # Perform action
            success = False
            action_verb = action.title()
            
            if action == "start":
                success = await ptero_client.start_server(target_server.id)
            elif action == "stop":
                success = await ptero_client.stop_server(target_server.id)
            elif action == "restart":
                success = await ptero_client.restart_server(target_server.id)
            elif action == "kill":
                success = await ptero_client.kill_server(target_server.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Server Action Successful",
                    description=f"Successfully {action_verb.lower()}ed server `{target_server.name}`",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Server",
                    value=f"**Name:** {target_server.name}\n**Identifier:** `{target_server.identifier}`",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action=f"server_{action}",
                    target_type="server",
                    target_id=target_server.id,
                    details={"server_name": target_server.name, "identifier": target_server.identifier},
                    success=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Failed to {action} server `{target_server.name}`. The server might already be in that state.",
                    ephemeral=True
                )
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action=f"server_{action}",
                    target_type="server",
                    target_id=target_server.id,
                    success=False,
                    error_message="Action failed"
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error performing action: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action=f"server_{action}",
                target_type="server",
                target_id=server_identifier,
                success=False,
                error_message=str(e)
            )
    
    @server.command(name="command", description="Send a command to server console")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        command="Command to send to the server"
    )
    async def server_command(self, interaction: discord.Interaction, 
                           server_identifier: str, command: str):
        """Send command to server console"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        if not user_config.can_manage_servers:
            await interaction.response.send_message(
                "You don't have permission to manage servers.",
                ephemeral=True
            )
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
                    f"❌ Server with identifier `{server_identifier}` not found.",
                    ephemeral=True
                )
                return
            
            # Send command
            success = await ptero_client.send_command(target_server.id, command)
            
            if success:
                embed = discord.Embed(
                    title="✅ Command Sent",
                    description=f"Command sent to server `{target_server.name}`",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Command",
                    value=f"```{command}```",
                    inline=False
                )
                embed.add_field(
                    name="Server",
                    value=f"**Name:** {target_server.name}\n**Identifier:** `{target_server.identifier}`",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="server_command",
                    target_type="server",
                    target_id=target_server.id,
                    details={"command": command, "server_name": target_server.name},
                    success=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Failed to send command to server `{target_server.name}`.",
                    ephemeral=True
                )
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="server_command",
                    target_type="server",
                    target_id=target_server.id,
                    success=False,
                    error_message="Command failed"
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error sending command: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="server_command",
                target_type="server",
                target_id=server_identifier,
                success=False,
                error_message=str(e)
            )
    
    def get_status_emoji(self, state: ServerState) -> str:
        """Get emoji for server state"""
        emoji_map = {
            ServerState.RUNNING: "🟢",
            ServerState.STOPPED: "🔴",
            ServerState.STARTING: "🟡",
            ServerState.STOPPING: "🟠",
            ServerState.RESTARTING: "🔄"
        }
        return emoji_map.get(state, "⚪")
    
    def get_status_color(self, state: ServerState) -> discord.Color:
        """Get color for server state"""
        color_map = {
            ServerState.RUNNING: discord.Color.green(),
            ServerState.STOPPED: discord.Color.red(),
            ServerState.STARTING: discord.Color.gold(),
            ServerState.STOPPING: discord.Color.orange(),
            ServerState.RESTARTING: discord.Color.blue()
        }
        return color_map.get(state, discord.Color.grey())
