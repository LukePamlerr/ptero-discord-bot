import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional
import datetime
import json

from bot.models import encryption_manager
from bot.database import get_db

class ScheduleCommands(commands.Cog):
    """Scheduling commands for automated server management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_tasks = {}  # In-memory storage for demo
    
    schedule = app_commands.Group(name="schedule", description="Schedule automated server tasks")
    
    @schedule.command(name="create", description="Create a scheduled task")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        action="Action to perform (start/stop/restart)",
        time="Time in HH:MM format (24-hour)",
        days="Days to run (comma-separated: mon,tue,wed,thu,fri,sat,sun)",
        repeat="Repeat weekly (true/false)"
    )
    async def schedule_create(self, interaction: discord.Interaction,
                          server_identifier: str, action: str, time: str,
                          days: str, repeat: bool = True):
        """Create a scheduled server task"""
        if not await self.bot.check_permissions(interaction):
            return
        
        # Validate action
        valid_actions = ["start", "stop", "restart", "kill"]
        if action.lower() not in valid_actions:
            await interaction.response.send_message(
                f"❌ Invalid action. Valid actions: {', '.join(valid_actions)}",
                ephemeral=True
            )
            return
        
        # Validate time format
        try:
            datetime.datetime.strptime(time, "%H:%M")
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid time format. Use HH:MM (24-hour format).",
                ephemeral=True
            )
            return
        
        # Validate days
        valid_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        day_list = [d.strip().lower() for d in days.split(",")]
        invalid_days = [d for d in day_list if d not in valid_days]
        
        if invalid_days:
            await interaction.response.send_message(
                f"❌ Invalid days: {', '.join(invalid_days)}. Valid days: {', '.join(valid_days)}",
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
            
            # Create schedule
            schedule_id = f"{user_id}_{server_identifier}_{datetime.datetime.now().timestamp()}"
            
            self.scheduled_tasks[schedule_id] = {
                "server_identifier": server_identifier,
                "server_name": target_server.name,
                "action": action.lower(),
                "time": time,
                "days": day_list,
                "repeat": repeat,
                "created_by": user_id,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            embed = discord.Embed(
                title="✅ Schedule Created",
                description=f"Successfully created scheduled task for `{target_server.name}`",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Schedule Details",
                value=(
                    f"**Server:** {target_server.name} ({server_identifier})\n"
                    f"**Action:** {action.title()}\n"
                    f"**Time:** {time}\n"
                    f"**Days:** {', '.join(day_list).title()}\n"
                    f"**Repeat:** {'Weekly' if repeat else 'One-time'}\n"
                    f"**Created by:** {interaction.user.display_name}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Information",
                value="This is a demonstration schedule. Actual scheduling would require persistent storage and a task runner.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="schedule_create",
                target_type="schedule",
                details={
                    "server_name": target_server.name,
                    "action": action,
                    "time": time,
                    "days": day_list,
                    "repeat": repeat
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating schedule: {str(e)}",
                ephemeral=True
            )
    
    @schedule.command(name="list", description="List all scheduled tasks")
    async def schedule_list(self, interaction: discord.Interaction):
        """List all scheduled tasks"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Filter schedules for this user
        user_schedules = {
            k: v for k, v in self.scheduled_tasks.items() 
            if v["created_by"] == user_id
        }
        
        if not user_schedules:
            embed = discord.Embed(
                title="📅 No Scheduled Tasks",
                description="You don't have any scheduled tasks.",
                color=discord.Color.orange()
            )
            
            embed.add_field(
                name="💡 Create a Schedule",
                value="Use `/schedule create` to create a new scheduled task.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📅 Scheduled Tasks",
            description=f"Found {len(user_schedules)} scheduled task(s)",
            color=discord.Color.blue()
        )
        
        for schedule_id, schedule in user_schedules.items():
            server_name = schedule["server_name"]
            action = schedule["action"].title()
            time = schedule["time"]
            days = ', '.join(schedule["days"]).title()
            repeat = "Weekly" if schedule["repeat"] else "One-time"
            
            field_value = (
                f"**Action:** {action}\n"
                f"**Time:** {time}\n"
                f"**Days:** {days}\n"
                f"**Repeat:** {repeat}\n"
                f"**Created:** {datetime.datetime.fromisoformat(schedule['created_at']).strftime('%Y-%m-%d')}"
            )
            
            embed.add_field(
                name=f"⏰ {server_name}",
                value=field_value,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @schedule.command(name="delete", description="Delete a scheduled task")
    @app_commands.describe(
        server_identifier="Server identifier of the scheduled task",
        confirm="Type 'DELETE' to confirm deletion"
    )
    async def schedule_delete(self, interaction: discord.Interaction,
                          server_identifier: str, confirm: str):
        """Delete a scheduled task"""
        if not await self.bot.check_permissions(interaction):
            return
        
        if confirm != "DELETE":
            await interaction.response.send_message(
                "❌ You must type 'DELETE' to confirm schedule deletion.",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Find and delete schedule
        to_delete = []
        for schedule_id, schedule in self.scheduled_tasks.items():
            if (schedule["created_by"] == user_id and 
                schedule["server_identifier"].lower() == server_identifier.lower()):
                to_delete.append((schedule_id, schedule))
        
        if not to_delete:
            await interaction.response.send_message(
                f"❌ No scheduled tasks found for server `{server_identifier}`.",
                ephemeral=True
            )
            return
        
        # Delete schedules
        for schedule_id, schedule in to_delete:
            del self.scheduled_tasks[schedule_id]
        
        embed = discord.Embed(
            title="✅ Schedule Deleted",
            description=f"Deleted {len(to_delete)} scheduled task(s) for server `{server_identifier}`",
            color=discord.Color.green()
        )
        
        for schedule_id, schedule in to_delete:
            embed.add_field(
                name=f"🗑️ Deleted Schedule",
                value=(
                    f"**Server:** {schedule['server_name']}\n"
                    f"**Action:** {schedule['action'].title()}\n"
                    f"**Time:** {schedule['time']}"
                ),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await self.bot.create_audit_log(
            discord_user_id=user_id,
            guild_id=guild_id,
            action="schedule_delete",
            target_type="schedule",
            details={
                "server_identifier": server_identifier,
                "deleted_count": len(to_delete)
            },
            success=True
        )

class AutomationCommands(commands.Cog):
    """Advanced automation commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    automation = app_commands.Group(name="automation", description="Advanced server automation")
    
    @automation.command(name="rules", description="Manage server automation rules")
    @app_commands.describe(
        server_identifier="Server identifier (e.g., mc123)",
        rule_type="Type of rule (cpu/memory/disk)",
        condition="Condition (greater_than/less_than)",
        threshold="Threshold value",
        action="Action to trigger (restart/notify/stop)"
    )
    async def automation_rules(self, interaction: discord.Interaction,
                            server_identifier: str, rule_type: str,
                            condition: str, threshold: float, action: str):
        """Create automation rules"""
        if not await self.bot.check_permissions(interaction):
            return
        
        # Validate inputs
        valid_types = ["cpu", "memory", "disk"]
        valid_conditions = ["greater_than", "less_than"]
        valid_actions = ["restart", "notify", "stop"]
        
        if rule_type.lower() not in valid_types:
            await interaction.response.send_message(
                f"❌ Invalid rule type. Valid: {', '.join(valid_types)}",
                ephemeral=True
            )
            return
        
        if condition.lower() not in valid_conditions:
            await interaction.response.send_message(
                f"❌ Invalid condition. Valid: {', '.join(valid_conditions)}",
                ephemeral=True
            )
            return
        
        if action.lower() not in valid_actions:
            await interaction.response.send_message(
                f"❌ Invalid action. Valid: {', '.join(valid_actions)}",
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
            
            # Create rule
            rule = {
                "server_identifier": server_identifier,
                "server_name": target_server.name,
                "rule_type": rule_type.lower(),
                "condition": condition.lower(),
                "threshold": threshold,
                "action": action.lower(),
                "created_by": user_id,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            embed = discord.Embed(
                title="✅ Automation Rule Created",
                description=f"Successfully created automation rule for `{target_server.name}`",
                color=discord.Color.green()
            )
            
            # Format rule description
            condition_symbol = ">" if condition == "greater_than" else "<"
            unit = "%" if rule_type == "cpu" else "MB"
            
            embed.add_field(
                name="🤖 Rule Details",
                value=(
                    f"**Server:** {target_server.name} ({server_identifier})\n"
                    f"**Rule:** When {rule_type.upper()} {condition_symbol} {threshold}{unit}\n"
                    f"**Action:** {action.title()}\n"
                    f"**Created by:** {interaction.user.display_name}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Information",
                value="This is a demonstration rule. Actual automation would require a monitoring service and rule engine.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="automation_rule_create",
                target_type="automation",
                details={
                    "server_name": target_server.name,
                    "rule_type": rule_type,
                    "condition": condition,
                    "threshold": threshold,
                    "action": action
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating automation rule: {str(e)}",
                ephemeral=True
            )
    
    @automation.command(name="status", description="Check automation system status")
    async def automation_status(self, interaction: discord.Interaction):
        """Check automation system status"""
        if not await self.bot.check_permissions(interaction):
            return
        
        embed = discord.Embed(
            title="🤖 Automation System Status",
            description="Current status of automation features",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Monitoring",
            value=(
                "**Status:** 🟢 Active\n"
                "**Update Interval:** 60 seconds\n"
                "**Monitored Metrics:** CPU, Memory, Disk, Network"
            ),
            inline=True
        )
        
        embed.add_field(
            name="⚙️ Automation Engine",
            value=(
                "**Status:** 🟢 Active\n"
                "**Rules Processed:** 0\n"
                "**Actions Triggered:** 0\n"
                "**Last Check:** Just now"
            ),
            inline=True
        )
        
        embed.add_field(
            name="🔧 System Health",
            value=(
                "**CPU Usage:** 2.1%\n"
                "**Memory Usage:** 45.2 MB\n"
                "**Uptime:** 2 days, 14 hours"
            ),
            inline=True
        )
        
        embed.add_field(
            name="ℹ️ Information",
            value="This is a demonstration status. Actual automation would show real metrics and system health.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
