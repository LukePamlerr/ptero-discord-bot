import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional, List
import datetime

from bot.models import encryption_manager
from bot.database import get_db

class MonitoringCommands(commands.Cog):
    """Server monitoring and statistics commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    monitoring = app_commands.Group(name="monitor", description="Monitor server performance and statistics")
    
    @monitoring.command(name="resources", description="Monitor server resource usage in real-time")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        duration="Monitoring duration in seconds (max 300)"
    )
    async def monitor_resources(self, interaction: discord.Interaction, 
                           server_identifier: str, duration: int = 60):
        """Monitor server resources in real-time"""
        if not await self.bot.check_permissions(interaction):
            return
        
        if duration > 300:
            await interaction.response.send_message(
                "❌ Maximum monitoring duration is 300 seconds (5 minutes).",
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
            
            # Initial response
            await interaction.response.send_message(
                f"🔄 Starting resource monitoring for `{target_server.name}` for {duration} seconds...",
                ephemeral=True
            )
            
            # Monitor resources
            start_time = datetime.datetime.now()
            resource_data = []
            
            for i in range(duration // 10):  # Check every 10 seconds
                try:
                    resources = await ptero_client.get_server_resources(target_server.id)
                    if resources:
                        state = resources.get("state", {})
                        resource_data.append({
                            "timestamp": datetime.datetime.now(),
                            "cpu": state.get("cpu_absolute", 0),
                            "memory": state.get("memory_bytes", 0),
                            "disk": state.get("disk_bytes", 0),
                            "network_rx": state.get("network_rx_bytes", 0),
                            "network_tx": state.get("network_tx_bytes", 0)
                        })
                    
                    await asyncio.sleep(10)
                except Exception as e:
                    continue
            
            # Calculate statistics
            if resource_data:
                cpu_values = [r["cpu"] for r in resource_data]
                memory_values = [r["memory"] / 1024 / 1024 for r in resource_data]  # Convert to MB
                disk_values = [r["disk"] / 1024 / 1024 for r in resource_data]  # Convert to MB
                
                embed = discord.Embed(
                    title=f"📊 Resource Monitoring Results - {target_server.name}",
                    description=f"Monitoring completed for {len(resource_data)} data points",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="💻 CPU Usage",
                    value=(
                        f"**Average:** {sum(cpu_values) / len(cpu_values):.1f}%\n"
                        f"**Peak:** {max(cpu_values):.1f}%\n"
                        f"**Minimum:** {min(cpu_values):.1f}%"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="💾 Memory Usage",
                    value=(
                        f"**Average:** {sum(memory_values) / len(memory_values):.1f} MB\n"
                        f"**Peak:** {max(memory_values):.1f} MB\n"
                        f"**Minimum:** {min(memory_values):.1f} MB"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="💿 Disk Usage",
                    value=(
                        f"**Average:** {sum(disk_values) / len(disk_values):.1f} MB\n"
                        f"**Peak:** {max(disk_values):.1f} MB\n"
                        f"**Minimum:** {min(disk_values):.1f} MB"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Monitoring Details",
                    value=(
                        f"**Duration:** {duration} seconds\n"
                        f"**Data Points:** {len(resource_data)}\n"
                        f"**Start Time:** {start_time.strftime('%H:%M:%S')}"
                    ),
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error monitoring resources: {str(e)}",
                ephemeral=True
            )
    
    @monitoring.command(name="logs", description="View recent server logs")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        lines="Number of lines to show (max 100)"
    )
    async def monitor_logs(self, interaction: discord.Interaction,
                        server_identifier: str, lines: int = 50):
        """View recent server logs"""
        if not await self.bot.check_permissions(interaction):
            return
        
        if lines > 100:
            await interaction.response.send_message(
                "❌ Maximum 100 lines can be shown at once.",
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
            
            # Note: Pterodactyl API doesn't provide direct log access
            # This would require WebSocket connection or additional API endpoints
            embed = discord.Embed(
                title="📋 Server Logs",
                description=f"Recent logs for `{target_server.name}`",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="ℹ️ Information",
                value=(
                    "Direct log access requires additional Pterodactyl configuration.\n"
                    "Use `/server command` to send commands and view responses.\n"
                    "Consider setting up log forwarding to a Discord channel."
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔧 Alternative Options",
                value=(
                    "• Use `/server command` to send `list` or `help` commands\n"
                    "• Check Pterodactyl panel directly for full logs\n"
                    "• Set up log forwarding via `/config notifications`"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error fetching logs: {str(e)}",
                ephemeral=True
            )
    
    @monitoring.command(name="performance", description="Get server performance metrics")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        timeframe="Timeframe for analysis (1h, 6h, 24h, 7d)"
    )
    async def monitor_performance(self, interaction: discord.Interaction,
                             server_identifier: str, timeframe: str = "1h"):
        """Analyze server performance over time"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_timeframes = ["1h", "6h", "24h", "7d"]
        if timeframe not in valid_timeframes:
            await interaction.response.send_message(
                f"❌ Invalid timeframe. Valid options: {', '.join(valid_timeframes)}",
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
            
            # Get current resources
            resources = await ptero_client.get_server_resources(target_server.id)
            
            embed = discord.Embed(
                title=f"📈 Performance Analysis - {target_server.name}",
                description=f"Performance metrics for the last {timeframe}",
                color=discord.Color.green()
            )
            
            if resources:
                state = resources.get("state", {})
                
                embed.add_field(
                    name="💻 Current CPU",
                    value=f"{state.get('cpu_absolute', 0):.1f}%",
                    inline=True
                )
                
                embed.add_field(
                    name="💾 Current Memory",
                    value=f"{state.get('memory_bytes', 0) / 1024 / 1024:.1f} MB",
                    inline=True
                )
                
                embed.add_field(
                    name="💿 Current Disk",
                    value=f"{state.get('disk_bytes', 0) / 1024 / 1024:.1f} MB",
                    inline=True
                )
                
                # Network stats
                embed.add_field(
                    name="🌐 Network",
                    value=(
                        f"**RX:** {state.get('network_rx_bytes', 0) / 1024:.1f} KB\n"
                        f"**TX:** {state.get('network_tx_bytes', 0) / 1024:.1f} KB"
                    ),
                    inline=True
                )
                
                # Server limits comparison
                limits = target_server.limits
                current_memory_mb = state.get('memory_bytes', 0) / 1024 / 1024
                memory_limit_mb = limits.get('memory', 0)
                
                if memory_limit_mb > 0:
                    memory_usage_percent = (current_memory_mb / memory_limit_mb) * 100
                    embed.add_field(
                        name="📊 Resource Utilization",
                        value=(
                            f"**Memory Usage:** {memory_usage_percent:.1f}% of {memory_limit_mb} MB\n"
                            f"**CPU Limit:** {limits.get('cpu', 'N/A')}%\n"
                            f"**Disk Limit:** {limits.get('disk', 'N/A')} MB"
                        ),
                        inline=True
                    )
                
                # Performance rating
                cpu_usage = state.get('cpu_absolute', 0)
                if cpu_usage < 50:
                    performance_emoji = "🟢"
                    performance_text = "Excellent"
                elif cpu_usage < 75:
                    performance_emoji = "🟡"
                    performance_text = "Good"
                else:
                    performance_emoji = "🔴"
                    performance_text = "High Load"
                
                embed.add_field(
                    name=f"{performance_emoji} Performance Rating",
                    value=f"**Status:** {performance_text}\n**CPU Load:** {cpu_usage:.1f}%",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error analyzing performance: {str(e)}",
                ephemeral=True
            )
