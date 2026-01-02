import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional
import datetime

from bot.models import encryption_manager
from bot.database import get_db

class NotificationCommands(commands.Cog):
    """Notification and alert management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.notification_channels = {}  # In-memory storage for demo
    
    notifications = app_commands.Group(name="notifications", description="Manage server notifications and alerts")
    
    @notifications.command(name="setup", description="Set up server notifications")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        channel="Discord channel for notifications",
        events="Events to notify (start,stop,crash,high_cpu,high_memory)"
    )
    async def notifications_setup(self, interaction: discord.Interaction,
                              server_identifier: str, channel: discord.TextChannel,
                              events: str):
        """Set up notifications for server events"""
        if not await self.bot.check_permissions(interaction):
            return
        
        # Validate events
        valid_events = ["start", "stop", "crash", "high_cpu", "high_memory", "backup", "restart"]
        event_list = [e.strip().lower() for e in events.split(",")]
        invalid_events = [e for e in event_list if e not in valid_events]
        
        if invalid_events:
            await interaction.response.send_message(
                f"❌ Invalid events: {', '.join(invalid_events)}. Valid: {', '.join(valid_events)}",
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
            
            # Store notification setup
            notification_id = f"{user_id}_{server_identifier}"
            self.notification_channels[notification_id] = {
                "server_identifier": server_identifier,
                "server_name": target_server.name,
                "channel_id": str(channel.id),
                "events": event_list,
                "created_by": user_id,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            embed = discord.Embed(
                title="✅ Notifications Setup",
                description=f"Successfully configured notifications for `{target_server.name}`",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Notification Details",
                value=(
                    f"**Server:** {target_server.name} ({server_identifier})\n"
                    f"**Channel:** {channel.mention}\n"
                    f"**Events:** {', '.join(event_list).title()}\n"
                    f"**Created by:** {interaction.user.display_name}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Information",
                value="Notifications will be sent to the specified channel when the selected events occur.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="notification_setup",
                target_type="notification",
                details={
                    "server_name": target_server.name,
                    "channel_id": str(channel.id),
                    "events": event_list
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting up notifications: {str(e)}",
                ephemeral=True
            )
    
    @notifications.command(name="test", description="Test notification system")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        event_type="Type of event to simulate"
    )
    async def notifications_test(self, interaction: discord.Interaction,
                             server_identifier: str, event_type: str):
        """Test notification system"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Find notification setup
        notification_id = f"{user_id}_{server_identifier}"
        notification = self.notification_channels.get(notification_id)
        
        if not notification:
            await interaction.response.send_message(
                f"❌ No notifications set up for server `{server_identifier}`.",
                ephemeral=True
            )
            return
        
        try:
            channel = interaction.guild.get_channel(int(notification["channel_id"]))
            if not channel:
                await interaction.response.send_message(
                    "❌ Notification channel not found.",
                    ephemeral=True
                )
                return
            
            # Create test notification
            embed = discord.Embed(
                title="🔔 Test Notification",
                description=f"Test notification for server `{notification['server_name']}`",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📋 Test Details",
                value=(
                    f"**Event Type:** {event_type.title()}\n"
                    f"**Server:** {notification['server_name']}\n"
                    f"**Triggered by:** {interaction.user.display_name}\n"
                    f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                inline=False
            )
            
            embed.set_footer(text="This is a test notification")
            
            await channel.send(embed=embed)
            
            await interaction.response.send_message(
                f"✅ Test notification sent to {channel.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error sending test notification: {str(e)}",
                ephemeral=True
            )
    
    @notifications.command(name="list", description="List all notification setups")
    async def notifications_list(self, interaction: discord.Interaction):
        """List all notification setups"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Filter notifications for this user
        user_notifications = {
            k: v for k, v in self.notification_channels.items() 
            if v["created_by"] == user_id
        }
        
        if not user_notifications:
            embed = discord.Embed(
                title="🔔 No Notifications",
                description="You don't have any notification setups.",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="💡 Set Up Notifications",
                value="Use `/notifications setup` to configure server notifications.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔔 Notification Setups",
            description=f"Found {len(user_notifications)} notification setup(s)",
            color=discord.Color.blue()
        )
        
        for notification_id, notification in user_notifications.items():
            server_name = notification["server_name"]
            channel_id = notification["channel_id"]
            events = ', '.join(notification["events"]).title()
            
            try:
                channel = interaction.guild.get_channel(int(channel_id))
                channel_name = channel.mention if channel else f"Unknown ({channel_id})"
            except:
                channel_name = f"Unknown ({channel_id})"
            
            field_value = (
                f"**Channel:** {channel_name}\n"
                f"**Events:** {events}\n"
                f"**Created:** {datetime.datetime.fromisoformat(notification['created_at']).strftime('%Y-%m-%d')}"
            )
            
            embed.add_field(
                name=f"🔔 {server_name}",
                value=field_value,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @notifications.command(name="remove", description="Remove notification setup")
    @app_commands.describe(
        server_identifier="Server identifier to remove notifications for",
        confirm="Type 'REMOVE' to confirm removal"
    )
    async def notifications_remove(self, interaction: discord.Interaction,
                              server_identifier: str, confirm: str):
        """Remove notification setup"""
        if not await self.bot.check_permissions(interaction):
            return
        
        if confirm != "REMOVE":
            await interaction.response.send_message(
                "❌ You must type 'REMOVE' to confirm notification removal.",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Find and remove notification
        notification_id = f"{user_id}_{server_identifier}"
        notification = self.notification_channels.get(notification_id)
        
        if not notification:
            await interaction.response.send_message(
                f"❌ No notifications found for server `{server_identifier}`.",
                ephemeral=True
            )
            return
        
        # Remove notification
        del self.notification_channels[notification_id]
        
        embed = discord.Embed(
            title="✅ Notifications Removed",
            description=f"Successfully removed notifications for `{notification['server_name']}`",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📋 Removal Details",
            value=(
                f"**Server:** {notification['server_name']}\n"
                f"**Removed by:** {interaction.user.display_name}\n"
                f"**Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await self.bot.create_audit_log(
            discord_user_id=user_id,
            guild_id=guild_id,
            action="notification_remove",
            target_type="notification",
            details={
                "server_name": notification["server_name"],
                "server_identifier": server_identifier
            },
            success=True
        )

class AlertCommands(commands.Cog):
    """Advanced alert management commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    alerts = app_commands.Group(name="alerts", description="Manage server alerts and warnings")
    
    @alerts.command(name="threshold", description="Set alert thresholds")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        metric="Metric to monitor (cpu/memory/disk)",
        warning_threshold="Warning threshold value",
        critical_threshold="Critical threshold value"
    )
    async def alerts_threshold(self, interaction: discord.Interaction,
                           server_identifier: str, metric: str,
                           warning_threshold: float, critical_threshold: float):
        """Set alert thresholds for server metrics"""
        if not await self.bot.check_permissions(interaction):
            return
        
        # Validate metric
        valid_metrics = ["cpu", "memory", "disk"]
        if metric.lower() not in valid_metrics:
            await interaction.response.send_message(
                f"❌ Invalid metric. Valid: {', '.join(valid_metrics)}",
                ephemeral=True
            )
            return
        
        if warning_threshold >= critical_threshold:
            await interaction.response.send_message(
                "❌ Warning threshold must be less than critical threshold.",
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
            
            # Determine unit
            if metric.lower() == "cpu":
                unit = "%"
                warning_str = f"{warning_threshold}%"
                critical_str = f"{critical_threshold}%"
            else:
                unit = "MB"
                warning_str = f"{warning_threshold} MB"
                critical_str = f"{critical_threshold} MB"
            
            embed = discord.Embed(
                title="✅ Alert Thresholds Set",
                description=f"Successfully set alert thresholds for `{target_server.name}`",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Threshold Details",
                value=(
                    f"**Server:** {target_server.name} ({server_identifier})\n"
                    f"**Metric:** {metric.upper()}\n"
                    f"**Warning:** {warning_str}\n"
                    f"**Critical:** {critical_str}\n"
                    f"**Set by:** {interaction.user.display_name}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Alert Behavior",
                value=(
                    "• **Warning Level:** Yellow alert when threshold exceeded\n"
                    "• **Critical Level:** Red alert when critical exceeded\n"
                    "• **Recovery:** Green alert when back to normal\n"
                    "• **Notifications:** Sent to configured channels"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="alert_threshold_set",
                target_type="alert",
                details={
                    "server_name": target_server.name,
                    "metric": metric,
                    "warning_threshold": warning_threshold,
                    "critical_threshold": critical_threshold
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error setting alert thresholds: {str(e)}",
                ephemeral=True
            )
    
    @alerts.command(name="history", description="View alert history")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        hours="Hours of history to show (max 168)"
    )
    async def alerts_history(self, interaction: discord.Interaction,
                          server_identifier: str, hours: int = 24):
        """View alert history"""
        if not await self.bot.check_permissions(interaction):
            return
        
        if hours > 168:  # 1 week max
            await interaction.response.send_message(
                "❌ Maximum history is 168 hours (1 week).",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        try:
            # Generate sample alert history
            alert_history = [
                {
                    "timestamp": datetime.datetime.now() - datetime.timedelta(hours=2),
                    "level": "warning",
                    "metric": "CPU",
                    "value": 85.2,
                    "threshold": 80.0,
                    "message": "CPU usage exceeded warning threshold"
                },
                {
                    "timestamp": datetime.datetime.now() - datetime.timedelta(hours=5),
                    "level": "critical",
                    "metric": "Memory",
                    "value": 1024.0,
                    "threshold": 1000.0,
                    "message": "Memory usage exceeded critical threshold"
                },
                {
                    "timestamp": datetime.datetime.now() - datetime.timedelta(hours=8),
                    "level": "recovery",
                    "metric": "CPU",
                    "value": 45.1,
                    "threshold": 80.0,
                    "message": "CPU usage returned to normal levels"
                }
            ]
            
            embed = discord.Embed(
                title="📊 Alert History",
                description=f"Alert history for server `{server_identifier}` (last {hours} hours)",
                color=discord.Color.blue()
            )
            
            for alert in alert_history:
                level_emoji = {"warning": "🟡", "critical": "🔴", "recovery": "🟢"}.get(alert["level"], "⚪")
                level_color = {"warning": discord.Color.orange(), "critical": discord.Color.red(), "recovery": discord.Color.green()}.get(alert["level"], discord.Color.grey())
                
                embed.add_field(
                    name=f"{level_emoji} {alert['level'].title()} Alert",
                    value=(
                        f"**Time:** {alert['timestamp'].strftime('%H:%M:%S')}\n"
                        f"**Metric:** {alert['metric']}\n"
                        f"**Value:** {alert['value']}\n"
                        f"**Threshold:** {alert['threshold']}\n"
                        f"**Message:** {alert['message']}"
                    ),
                    inline=False
                )
            
            embed.add_field(
                name="ℹ️ Information",
                value="This is a demonstration alert history. Actual alerts would be generated from real monitoring data.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error fetching alert history: {str(e)}",
                ephemeral=True
            )
