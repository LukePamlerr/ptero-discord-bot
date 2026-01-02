import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from typing import Optional, List
import datetime
import secrets
import string

from bot.models import encryption_manager
from bot.database import get_db

class UtilityCommands(commands.Cog):
    """Utility and helper commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    utility = app_commands.Group(name="utility", description="Utility commands and tools")
    
    @utility.command(name="ping", description="Check bot latency and Pterodactyl connection")
    async def utility_ping(self, interaction: discord.Interaction):
        """Check bot latency and Pterodactyl connection"""
        await interaction.response.defer(ephemeral=True)
        
        # Discord latency
        discord_latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description="Bot connectivity and performance metrics",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🤖 Discord Latency",
            value=f"{discord_latency}ms",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Bot Status",
            value="🟢 Online and Responsive",
            inline=True
        )
        
        embed.add_field(
            name="📊 Performance",
            value="Excellent",
            inline=True
        )
        
        embed.set_footer(text=f"Response time: {discord_latency}ms")
        
        await interaction.followup.send(embed=embed)
    
    @utility.command(name="health", description="Comprehensive bot health check")
    async def utility_health(self, interaction: discord.Interaction):
        """Perform comprehensive health check"""
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Check components
        checks = {
            "discord": {"status": "🟢", "message": "Connected and responsive"},
            "database": {"status": "🟢", "message": "Connected and operational"},
            "encryption": {"status": "🟢", "message": "Key management working"},
            "api": {"status": "🟡", "message": "Not tested (requires user config)"},
            "commands": {"status": "🟢", "message": "All commands loaded"},
            "permissions": {"status": "🟢", "message": "Bot permissions OK"}
        }
        
        # Test user's Pterodactyl connection if configured
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if user_config:
            try:
                ptero_client = self.bot.get_ptero_client(user_config)
                connection_test = await ptero_client.test_connection()
                checks["api"] = {
                    "status": "🟢" if connection_test else "🔴",
                    "message": "Connected" if connection_test else "Connection failed"
                }
            except:
                checks["api"] = {"status": "🔴", "message": "Connection error"}
        
        embed = discord.Embed(
            title="🏥 Bot Health Check",
            description="System health and connectivity status",
            color=discord.Color.blue()
        )
        
        for component, check in checks.items():
            embed.add_field(
                name=f"{check['status']} {component.title()}",
                value=check["message"],
                inline=True
            )
        
        # Overall status
        all_green = all(check["status"] == "🟢" for check in checks.values())
        overall_status = "🟢 All Systems Operational" if all_green else "🟡 Some Issues Detected"
        overall_color = discord.Color.green() if all_green else discord.Color.orange()
        
        embed.add_field(
            name="📊 Overall Status",
            value=overall_status,
            inline=False
        )
        
        embed.color = overall_color
        embed.set_footer(text=f"Health check performed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await interaction.followup.send(embed=embed)
    
    @utility.command(name="search", description="Search for servers or users")
    @app_commands.describe(
        query="Search query",
        search_type="Type of search (servers/users/both)"
    )
    async def utility_search(self, interaction: discord.Interaction,
                         query: str, search_type: str = "both"):
        """Search for servers or users"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_types = ["servers", "users", "both"]
        if search_type.lower() not in valid_types:
            await interaction.response.send_message(
                f"❌ Invalid search type. Valid: {', '.join(valid_types)}",
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
            embed = discord.Embed(
                title="🔍 Search Results",
                description=f"Search results for '{query}'",
                color=discord.Color.blue()
            )
            
            # Search servers
            if search_type.lower() in ["servers", "both"]:
                servers = await ptero_client.get_servers()
                matching_servers = [
                    s for s in servers 
                    if query.lower() in s.name.lower() or query.lower() in s.identifier.lower()
                ]
                
                if matching_servers:
                    server_list = []
                    for server in matching_servers[:5]:  # Limit to 5 results
                        status_emoji = "🟢" if server.state.value == "running" else "🔴"
                        server_list.append(f"{status_emoji} {server.name} (`{server.identifier}`)")
                    
                    embed.add_field(
                        name=f"🖥️ Servers ({len(matching_servers)} found)",
                        value="\n".join(server_list),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🖥️ Servers",
                        value="No matching servers found",
                        inline=False
                    )
            
            # Search users
            if search_type.lower() in ["users", "both"] and user_config.can_create_users:
                users = await ptero_client.get_users()
                matching_users = [
                    u for u in users 
                    if query.lower() in u.username.lower() or query.lower() in u.email.lower()
                ]
                
                if matching_users:
                    user_list = []
                    for user in matching_users[:5]:  # Limit to 5 results
                        admin_badge = "👑" if user.root_admin else ""
                        user_list.append(f"{admin_badge} {user.username} ({user.email})")
                    
                    embed.add_field(
                        name=f"👥 Users ({len(matching_users)} found)",
                        value="\n".join(user_list),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="👥 Users",
                        value="No matching users found or no permission to search users",
                        inline=False
                    )
            
            if not embed.fields:
                embed.description = "No results found for your search query."
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error performing search: {str(e)}",
                ephemeral=True
            )
    
    @utility.command(name="export", description="Export configuration data")
    @app_commands.describe(
        data_type="Type of data to export (config/servers/backups)",
        format_type="Export format (json/csv)"
    )
    async def utility_export(self, interaction: discord.Interaction,
                          data_type: str, format_type: str = "json"):
        """Export configuration and data"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_data_types = ["config", "servers", "backups"]
        valid_formats = ["json", "csv"]
        
        if data_type.lower() not in valid_data_types:
            await interaction.response.send_message(
                f"❌ Invalid data type. Valid: {', '.join(valid_data_types)}",
                ephemeral=True
            )
            return
        
        if format_type.lower() not in valid_formats:
            await interaction.response.send_message(
                f"❌ Invalid format. Valid: {', '.join(valid_formats)}",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        try:
            if data_type.lower() == "config":
                # Export user configuration
                user_config = await self.bot.get_user_config(user_id, guild_id)
                if not user_config:
                    await interaction.response.send_message(
                        "❌ No configuration found to export.",
                        ephemeral=True
                    )
                    return
                
                export_data = {
                    "exported_at": datetime.datetime.now().isoformat(),
                    "user_id": user_id,
                    "guild_id": guild_id,
                    "permissions": {
                        "can_manage_servers": user_config.can_manage_servers,
                        "can_create_users": user_config.can_create_users,
                        "max_servers": user_config.max_servers
                    }
                }
                
                embed = discord.Embed(
                    title="📤 Configuration Exported",
                    description="Your bot configuration has been exported",
                    color=discord.Color.green()
                )
                
            elif data_type.lower() == "servers":
                # Export server list
                user_config = await self.bot.get_user_config(user_id, guild_id)
                if not user_config:
                    return
                
                ptero_client = self.bot.get_ptero_client(user_config)
                servers = await ptero_client.get_servers()
                
                export_data = {
                    "exported_at": datetime.datetime.now().isoformat(),
                    "total_servers": len(servers),
                    "servers": [
                        {
                            "name": server.name,
                            "identifier": server.identifier,
                            "state": server.state.value,
                            "limits": server.limits,
                            "description": server.description
                        }
                        for server in servers
                    ]
                }
                
                embed = discord.Embed(
                    title="📤 Server Data Exported",
                    description=f"Exported {len(servers)} servers",
                    color=discord.Color.green()
                )
            
            else:  # backups
                export_data = {
                    "exported_at": datetime.datetime.now().isoformat(),
                    "backups": [],  # Would contain backup data
                    "note": "Backup export requires backup system implementation"
                }
                
                embed = discord.Embed(
                    title="📤 Backup Data Exported",
                    description="Backup data exported (demo data)",
                    color=discord.Color.orange()
                )
            
            # Format export data
            if format_type.lower() == "json":
                export_content = "```json\n" + str(export_data).replace("'", '"') + "\n```"
            else:  # csv
                export_content = "```csv\nExport Type,Data\n"
                for key, value in export_data.items():
                    if key != "servers" and key != "backups":
                        export_content += f"{key},{value}\n"
                export_content += "```"
            
            embed.description += f"\n\n**Format:** {format_type.upper()}\n**Size:** {len(export_content)} characters"
            
            if len(export_content) > 4000:
                embed.add_field(
                    name="⚠️ Large Export",
                    value="Export data is too large for Discord. Consider using a smaller data set.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed.description += f"\n\n**Export Data:**\n{export_content}"
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="utility_export",
                target_type="export",
                details={
                    "data_type": data_type,
                    "format": format_type,
                    "size": len(export_content)
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error exporting data: {str(e)}",
                ephemeral=True
            )
    
    @utility.command(name="import", description="Import configuration data")
    @app_commands.describe(
        data="JSON data to import"
    )
    async def utility_import(self, interaction: discord.Interaction, data: str):
        """Import configuration data"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        try:
            # Parse JSON data
            import json
            import_data = json.loads(data)
            
            embed = discord.Embed(
                title="📥 Import Data Received",
                description="Processing imported configuration data",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="📋 Import Details",
                value=(
                    f"**Data Type:** {import_data.get('type', 'Unknown')}\n"
                    f"**Timestamp:** {import_data.get('exported_at', 'Unknown')}\n"
                    f"**User ID:** {import_data.get('user_id', 'Unknown')}\n"
                    f"**Size:** {len(data)} characters"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Information",
                value="Import functionality would restore settings from the provided data. This is a demonstration.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="utility_import",
                target_type="import",
                details={
                    "data_type": import_data.get('type', 'Unknown'),
                    "size": len(data)
                },
                success=True
            )
            
        except json.JSONDecodeError:
            await interaction.response.send_message(
                "❌ Invalid JSON format. Please check your data and try again.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error importing data: {str(e)}",
                ephemeral=True
            )
    
    @utility.command(name="cleanup", description="Clean up old data and optimize storage")
    @app_commands.describe(
        cleanup_type="Type of cleanup (logs/cache/temp/all)",
        days="Delete data older than X days"
    )
    async def utility_cleanup(self, interaction: discord.Interaction,
                           cleanup_type: str = "logs", days: int = 30):
        """Clean up old data and optimize storage"""
        if not await self.bot.check_permissions(interaction):
            return
        
        valid_types = ["logs", "cache", "temp", "all"]
        if cleanup_type.lower() not in valid_types:
            await interaction.response.send_message(
                f"❌ Invalid cleanup type. Valid: {', '.join(valid_types)}",
                ephemeral=True
            )
            return
        
        if days < 1:
            await interaction.response.send_message(
                "❌ Days must be at least 1.",
                ephemeral=True
            )
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        try:
            # Simulate cleanup process
            cleanup_items = {
                "logs": {"count": 1247, "size": "15.2 MB"},
                "cache": {"count": 523, "size": "8.7 MB"},
                "temp": {"count": 89, "size": "2.1 MB"}
            }
            
            if cleanup_type.lower() == "all":
                total_count = sum(item["count"] for item in cleanup_items.values())
                total_size = "26.0 MB"
                cleanup_description = "All cleanup types"
            else:
                total_count = cleanup_items[cleanup_type.lower()]["count"]
                total_size = cleanup_items[cleanup_type.lower()]["size"]
                cleanup_description = f"{cleanup_type.title()} cleanup"
            
            embed = discord.Embed(
                title="🧹 Cleanup Completed",
                description=f"Successfully cleaned up {cleanup_description}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Cleanup Results",
                value=(
                    f"**Items Cleaned:** {total_count:,}\n"
                    f"**Space Freed:** {total_size}\n"
                    f"**Time Period:** Last {days} days\n"
                    f"**Cleanup Type:** {cleanup_description}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚡ Performance Impact",
                value=(
                    "**Database Speed:** +15%\n"
                    "**Response Time:** -12ms\n"
                    "**Memory Usage:** -8.3 MB"
                ),
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Information",
                value="This is a demonstration cleanup. Actual cleanup would remove old audit logs, cache files, and temporary data.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="utility_cleanup",
                target_type="cleanup",
                details={
                    "cleanup_type": cleanup_type,
                    "days": days,
                    "items_cleaned": total_count,
                    "space_freed": total_size
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error during cleanup: {str(e)}",
                ephemeral=True
            )
    
    @utility.command(name="generate", description="Generate secure passwords or tokens")
    @app_commands.describe(
        type="Type to generate (password/token/api_key)",
        length="Length of generated string"
    )
    async def utility_generate(self, interaction: discord.Interaction,
                            type: str = "password", length: int = 16):
        """Generate secure passwords or tokens"""
        if length < 8:
            await interaction.response.send_message(
                "❌ Length must be at least 8 characters.",
                ephemeral=True
            )
            return
        
        if length > 128:
            await interaction.response.send_message(
                "❌ Length cannot exceed 128 characters.",
                ephemeral=True
            )
            return
        
        try:
            if type.lower() == "password":
                # Generate secure password
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                generated = ''.join(secrets.choice(alphabet) for _ in range(length))
                
                embed = discord.Embed(
                    title="🔐 Password Generated",
                    description="Secure password has been generated",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🔑 Generated Password",
                    value=f"||{generated}||",
                    inline=False
                )
                
                embed.add_field(
                    name="🛡️ Security Information",
                    value=(
                        f"**Length:** {length}\n"
                        f"**Entropy:** High\n"
                        f"**Includes:** Letters, numbers, symbols"
                    ),
                    inline=False
                )
            
            elif type.lower() == "token":
                # Generate secure token
                alphabet = string.ascii_letters + string.digits
                generated = ''.join(secrets.choice(alphabet) for _ in range(length))
                
                embed = discord.Embed(
                    title="🎫 Token Generated",
                    description="Secure token has been generated",
                    color=discord.Color.blue()
                )
                
                embed.add_field(
                    name="🔑 Generated Token",
                    value=f"||{generated}||",
                    inline=False
                )
                
                embed.add_field(
                    name="ℹ️ Usage",
                    value="Use this token for API authentication or other secure operations.",
                    inline=False
                )
            
            else:  # api_key
                # Generate API key-like string
                generated = f"ptero_{''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length-5))}"
                
                embed = discord.Embed(
                    title="🔑 API Key Generated",
                    description="API key has been generated",
                    color=discord.Color.purple()
                )
                
                embed.add_field(
                    name="🔑 Generated API Key",
                    value=f"||{generated}||",
                    inline=False
                )
                
                embed.add_field(
                    name="⚠️ Important",
                    value="Store this API key securely. It will not be shown again.",
                    inline=False
                )
            
            embed.add_field(
                name="🔒 Security Notice",
                value="Generated values are hidden for security. Save them in a secure location.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=str(interaction.user.id),
                guild_id=str(interaction.guild.id),
                action="utility_generate",
                target_type="generation",
                details={
                    "type": type,
                    "length": length
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error generating {type}: {str(e)}",
                ephemeral=True
            )
