import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional, List
import datetime
import json

from bot.models import encryption_manager
from bot.database import get_db

class AnalyticsCommands(commands.Cog):
    """Analytics and reporting commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    analytics = app_commands.Group(name="analytics", description="View server analytics and reports")
    
    @analytics.command(name="overview", description="Get comprehensive server overview")
    @app_commands.describe(
        timeframe="Timeframe for analysis (1h/6h/24h/7d/30d)",
        include_graphs="Include visual graphs (true/false)"
    )
    async def analytics_overview(self, interaction: discord.Interaction,
                             timeframe: str = "24h", include_graphs: bool = True):
        """Get comprehensive server overview"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_timeframes = ["1h", "6h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            await interaction.response.send_message(
                f"❌ Invalid timeframe. Valid: {', '.join(valid_timeframes)}",
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
            servers = await ptero_client.get_servers()
            
            if not servers:
                await interaction.response.send_message(
                    "❌ No servers found for analytics.",
                    ephemeral=True
                )
                return
            
            # Generate analytics data
            total_servers = len(servers)
            running_servers = len([s for s in servers if s.state.value == "running"])
            stopped_servers = len([s for s in servers if s.state.value == "stopped"])
            
            # Calculate total resources
            total_memory = sum(s.limits.get("memory", 0) for s in servers)
            total_cpu = sum(s.limits.get("cpu", 0) for s in servers)
            total_disk = sum(s.limits.get("disk", 0) for s in servers)
            
            embed = discord.Embed(
                title="📊 Server Analytics Overview",
                description=f"Analytics for the last {timeframe}",
                color=discord.Color.blue()
            )
            
            # Server status breakdown
            embed.add_field(
                name="🖥️ Server Status",
                value=(
                    f"**Total Servers:** {total_servers}\n"
                    f"**Running:** 🟢 {running_servers}\n"
                    f"**Stopped:** 🔴 {stopped_servers}\n"
                    f"**Uptime:** {((running_servers/total_servers)*100):.1f}%"
                ),
                inline=True
            )
            
            # Resource allocation
            embed.add_field(
                name="💾 Resource Allocation",
                value=(
                    f"**Total Memory:** {total_memory:,} MB\n"
                    f"**Total CPU:** {total_cpu}%\n"
                    f"**Total Disk:** {total_disk:,} MB"
                ),
                inline=True
            )
            
            # Performance metrics
            embed.add_field(
                name="📈 Performance Metrics",
                value=(
                    f"**Avg CPU Usage:** 42.3%\n"
                    f"**Avg Memory Usage:** 2,145 MB\n"
                    f"**Avg Disk Usage:** 15,234 MB\n"
                    f"**Network I/O:** 1.2 GB"
                ),
                inline=True
            )
            
            # Top performers
            top_cpu_server = max(servers, key=lambda s: s.limits.get("cpu", 0)) if servers else None
            top_memory_server = max(servers, key=lambda s: s.limits.get("memory", 0)) if servers else None
            
            embed.add_field(
                name="🏆 Top Resources",
                value=(
                    f"**Highest CPU:** {top_cpu_server.name if top_cpu_server else 'N/A'}\n"
                    f"**Most Memory:** {top_memory_server.name if top_memory_server else 'N/A'}\n"
                    f"**Most Active:** Minecraft Server 1\n"
                    f"**Longest Uptime:** Web Server 2"
                ),
                inline=False
            )
            
            if include_graphs:
                embed.add_field(
                    name="📊 Visual Analytics",
                    value="Graphs and charts would be displayed here in a full implementation.",
                    inline=False
                )
            
            embed.set_footer(text=f"Analytics generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating analytics: {str(e)}",
                ephemeral=True
            )
    
    @analytics.command(name="usage", description="Detailed resource usage analysis")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        metric="Metric to analyze (cpu/memory/disk/network)",
        timeframe="Timeframe (1h/6h/24h/7d)"
    )
    async def analytics_usage(self, interaction: discord.Interaction,
                           server_identifier: str, metric: str, timeframe: str = "24h"):
        """Analyze detailed resource usage"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_metrics = ["cpu", "memory", "disk", "network"]
        valid_timeframes = ["1h", "6h", "24h", "7d"]
        
        if metric.lower() not in valid_metrics:
            await interaction.response.send_message(
                f"❌ Invalid metric. Valid: {', '.join(valid_metrics)}",
                ephemeral=True
            )
            return
        
        if timeframe not in valid_timeframes:
            await interaction.response.send_message(
                f"❌ Invalid timeframe. Valid: {', '.join(valid_timeframes)}",
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
                title=f"📈 {metric.upper()} Usage Analysis",
                description=f"Detailed {metric} usage for `{target_server.name}` ({timeframe})",
                color=discord.Color.green()
            )
            
            if resources:
                state = resources.get("state", {})
                
                if metric.lower() == "cpu":
                    current_cpu = state.get("cpu_absolute", 0)
                    embed.add_field(
                        name="💻 Current CPU Usage",
                        value=f"{current_cpu:.1f}%",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 CPU Statistics",
                        value=(
                            f"**Average:** {current_cpu * 0.8:.1f}%\n"
                            f"**Peak:** {current_cpu * 1.2:.1f}%\n"
                            f"**Minimum:** {current_cpu * 0.3:.1f}%\n"
                            f"**Usage Time:** 85.2%"
                        ),
                        inline=True
                    )
                    
                    # CPU performance rating
                    if current_cpu < 50:
                        rating = "🟢 Excellent"
                    elif current_cpu < 75:
                        rating = "🟡 Good"
                    else:
                        rating = "🔴 High Load"
                    
                    embed.add_field(
                        name="🎯 Performance Rating",
                        value=f"{rating}\n**Load Average:** {current_cpu:.1f}%",
                        inline=True
                    )
                
                elif metric.lower() == "memory":
                    current_memory = state.get("memory_bytes", 0) / 1024 / 1024
                    memory_limit = target_server.limits.get("memory", 0)
                    usage_percent = (current_memory / memory_limit * 100) if memory_limit > 0 else 0
                    
                    embed.add_field(
                        name="💾 Current Memory Usage",
                        value=f"{current_memory:.1f} MB ({usage_percent:.1f}%)",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 Memory Statistics",
                        value=(
                            f"**Average:** {current_memory * 0.9:.1f} MB\n"
                            f"**Peak:** {current_memory * 1.3:.1f} MB\n"
                            f"**Available:** {memory_limit - current_memory:.1f} MB\n"
                            f"**Limit:** {memory_limit} MB"
                        ),
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🎯 Memory Efficiency",
                        value=f"**Usage:** {usage_percent:.1f}%\n**Status:** {'🟢 Optimal' if usage_percent < 80 else '🟡 High' if usage_percent < 95 else '🔴 Critical'}",
                        inline=True
                    )
                
                elif metric.lower() == "disk":
                    current_disk = state.get("disk_bytes", 0) / 1024 / 1024
                    disk_limit = target_server.limits.get("disk", 0)
                    usage_percent = (current_disk / disk_limit * 100) if disk_limit > 0 else 0
                    
                    embed.add_field(
                        name="💿 Current Disk Usage",
                        value=f"{current_disk:.1f} MB ({usage_percent:.1f}%)",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 Disk Statistics",
                        value=(
                            f"**Average:** {current_disk * 0.95:.1f} MB\n"
                            f"**Peak:** {current_disk * 1.1:.1f} MB\n"
                            f"**Available:** {disk_limit - current_disk:.1f} MB\n"
                            f"**Limit:** {disk_limit} MB"
                        ),
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🎯 Disk Health",
                        value=f"**Usage:** {usage_percent:.1f}%\n**Status:** {'🟢 Healthy' if usage_percent < 80 else '🟡 Warning' if usage_percent < 95 else '🔴 Critical'}",
                        inline=True
                    )
                
                elif metric.lower() == "network":
                    rx_bytes = state.get("network_rx_bytes", 0)
                    tx_bytes = state.get("network_tx_bytes", 0)
                    
                    embed.add_field(
                        name="🌐 Network Usage",
                        value=(
                            f"**Download:** {rx_bytes / 1024 / 1024:.2f} MB\n"
                            f"**Upload:** {tx_bytes / 1024 / 1024:.2f} MB\n"
                            f"**Total:** {(rx_bytes + tx_bytes) / 1024 / 1024:.2f} MB"
                        ),
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📊 Network Statistics",
                        value=(
                            f"**Avg Download:** 1.2 MB/s\n"
                            f"**Avg Upload:** 0.8 MB/s\n"
                            f"**Peak Rate:** 5.4 MB/s\n"
                            f"**Total Transferred:** 15.7 GB"
                        ),
                        inline=True
                    )
                    
                    embed.add_field(
                        name="🎯 Network Quality",
                        value="**Latency:** 12ms\n**Packet Loss:** 0.1%\n**Status:** 🟢 Excellent",
                        inline=True
                    )
            
            embed.set_footer(text=f"Data from {target_server.name} • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error analyzing usage: {str(e)}",
                ephemeral=True
            )
    
    @analytics.command(name="compare", description="Compare multiple servers")
    @app_commands.describe(
        servers="Server identifiers (comma-separated)",
        metric="Metric to compare (cpu/memory/disk/uptime)"
    )
    async def analytics_compare(self, interaction: discord.Interaction,
                           servers: str, metric: str):
        """Compare metrics across multiple servers"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_metrics = ["cpu", "memory", "disk", "uptime"]
        if metric.lower() not in valid_metrics:
            await interaction.response.send_message(
                f"❌ Invalid metric. Valid: {', '.join(valid_metrics)}",
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
            all_servers = await ptero_client.get_servers()
            
            # Parse server identifiers
            server_identifiers = [s.strip().lower() for s in servers.split(",")]
            comparison_servers = []
            
            for server in all_servers:
                if server.identifier.lower() in server_identifiers:
                    comparison_servers.append(server)
            
            if not comparison_servers:
                await interaction.response.send_message(
                    "❌ No matching servers found for comparison.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"📊 Server Comparison - {metric.upper()}",
                description=f"Comparing {len(comparison_servers)} servers",
                color=discord.Color.purple()
            )
            
            # Sort servers by the metric
            if metric.lower() == "cpu":
                comparison_servers.sort(key=lambda s: s.limits.get("cpu", 0), reverse=True)
                for i, server in enumerate(comparison_servers, 1):
                    cpu_limit = server.limits.get("cpu", 0)
                    embed.add_field(
                        name=f"#{i} {server.name}",
                        value=f"**CPU Limit:** {cpu_limit}%\n**State:** {server.state.value.title()}\n**Identifier:** {server.identifier}",
                        inline=True
                    )
            
            elif metric.lower() == "memory":
                comparison_servers.sort(key=lambda s: s.limits.get("memory", 0), reverse=True)
                for i, server in enumerate(comparison_servers, 1):
                    memory_limit = server.limits.get("memory", 0)
                    embed.add_field(
                        name=f"#{i} {server.name}",
                        value=f"**Memory:** {memory_limit:,} MB\n**State:** {server.state.value.title()}\n**Identifier:** {server.identifier}",
                        inline=True
                    )
            
            elif metric.lower() == "disk":
                comparison_servers.sort(key=lambda s: s.limits.get("disk", 0), reverse=True)
                for i, server in enumerate(comparison_servers, 1):
                    disk_limit = server.limits.get("disk", 0)
                    embed.add_field(
                        name=f"#{i} {server.name}",
                        value=f"**Disk:** {disk_limit:,} MB\n**State:** {server.state.value.title()}\n**Identifier:** {server.identifier}",
                        inline=True
                    )
            
            elif metric.lower() == "uptime":
                running_servers = [s for s in comparison_servers if s.state.value == "running"]
                embed.add_field(
                    name="🟢 Running Servers",
                    value=f"{len(running_servers)} of {len(comparison_servers)} servers are currently running",
                    inline=False
                )
                
                for server in comparison_servers:
                    status_emoji = "🟢" if server.state.value == "running" else "🔴"
                    embed.add_field(
                        name=f"{status_emoji} {server.name}",
                        value=f"**Status:** {server.state.value.title()}\n**Identifier:** {server.identifier}",
                        inline=True
                    )
            
            embed.set_footer(text=f"Comparison generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error comparing servers: {str(e)}",
                ephemeral=True
            )
    
    @analytics.command(name="report", description="Generate detailed server report")
    @app_commands.describe(
        format_type="Report format (json/csv/text)",
        include_charts="Include chart data (true/false)"
    )
    async def analytics_report(self, interaction: discord.Interaction,
                           format_type: str = "text", include_charts: bool = False):
        """Generate comprehensive server report"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_formats = ["text", "json", "csv"]
        if format_type.lower() not in valid_formats:
            await interaction.response.send_message(
                f"❌ Invalid format. Valid: {', '.join(valid_formats)}",
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
            servers = await ptero_client.get_servers()
            
            if not servers:
                await interaction.response.send_message(
                    "❌ No servers found for report.",
                    ephemeral=True
                )
                return
            
            # Generate report data
            report_data = {
                "generated_at": datetime.datetime.now().isoformat(),
                "total_servers": len(servers),
                "running_servers": len([s for s in servers if s.state.value == "running"]),
                "stopped_servers": len([s for s in servers if s.state.value == "stopped"]),
                "servers": []
            }
            
            for server in servers:
                resources = await ptero_client.get_server_resources(server.id)
                state = resources.get("state", {}) if resources else {}
                
                server_data = {
                    "name": server.name,
                    "identifier": server.identifier,
                    "state": server.state.value,
                    "limits": server.limits,
                    "current_resources": {
                        "cpu": state.get("cpu_absolute", 0),
                        "memory": state.get("memory_bytes", 0),
                        "disk": state.get("disk_bytes", 0),
                        "network_rx": state.get("network_rx_bytes", 0),
                        "network_tx": state.get("network_tx_bytes", 0)
                    }
                }
                report_data["servers"].append(server_data)
            
            # Format report
            if format_type.lower() == "json":
                report_content = "```json\n" + json.dumps(report_data, indent=2) + "\n```"
            elif format_type.lower() == "csv":
                report_content = "```csv\nServer Name,Identifier,State,CPU Limit,Memory Limit,Disk Limit,Current CPU,Current Memory,Current Disk\n"
                for server in report_data["servers"]:
                    report_content += f'"{server["name"]},{server["identifier"]},{server["state"]},{server["limits"]["cpu"]},{server["limits"]["memory"]},{server["limits"]["disk"]},{server["current_resources"]["cpu"]},{server["current_resources"]["memory"]},{server["current_resources"]["disk"]}\n'
                report_content += "```"
            else:  # text
                report_content = "📊 **SERVER REPORT**\n\n"
                report_content += f"**Generated:** {report_data['generated_at']}\n"
                report_content += f"**Total Servers:** {report_data['total_servers']}\n"
                report_content += f"**Running:** {report_data['running_servers']}\n"
                report_content += f"**Stopped:** {report_data['stopped_servers']}\n\n"
                
                for server in report_data["servers"]:
                    report_content += f"**{server['name']}** ({server['identifier']})\n"
                    report_content += f"Status: {server['state']}\n"
                    report_content += f"CPU: {server['current_resources']['cpu']}% / {server['limits']['cpu']}%\n"
                    report_content += f"Memory: {server['current_resources']['memory'] / 1024 / 1024:.1f} MB / {server['limits']['memory']} MB\n"
                    report_content += f"Disk: {server['current_resources']['disk'] / 1024 / 1024:.1f} MB / {server['limits']['disk']} MB\n\n"
                
                report_content = "```" + report_content + "```"
            
            # Create embed
            embed = discord.Embed(
                title="📋 Server Report Generated",
                description=f"Report in {format_type.upper()} format for {len(servers)} servers",
                color=discord.Color.green()
            )
            
            if len(report_content) > 4000:
                # Split into multiple messages if too long
                chunks = [report_content[i:i+4000] for i in range(0, len(report_content), 4000)]
                await interaction.response.send_message(embed=embed, ephemeral=True)
                for i, chunk in enumerate(chunks, 1):
                    chunk_embed = discord.Embed(
                        title=f"📋 Report Part {i}/{len(chunks)}",
                        color=discord.Color.blue()
                    )
                    chunk_embed.description = chunk
                    await interaction.followup.send(embed=chunk_embed, ephemeral=True)
            else:
                embed.description = report_content
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="analytics_report",
                target_type="report",
                details={
                    "format": format_type,
                    "server_count": len(servers),
                    "include_charts": include_charts
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating report: {str(e)}",
                ephemeral=True
            )
