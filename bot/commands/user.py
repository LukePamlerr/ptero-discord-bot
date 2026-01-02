import discord
from discord import app_commands
from discord.ext import commands
import secrets
import string
from typing import Optional

from bot.models import encryption_manager
from bot.database import get_db

class UserCommands(commands.Cog):
    """User management commands for Pterodactyl"""
    
    def __init__(self, bot):
        self.bot = bot
    
    user = app_commands.Group(name="user", description="Manage Pterodactyl users")
    
    @user.command(name="create", description="Create a new Pterodactyl user")
    @app_commands.describe(
        username="Username for the new user",
        email="Email address for the new user",
        first_name="First name of the user",
        last_name="Last name of the user",
        password="Password for the new user (optional, will generate if not provided)"
    )
    async def user_create(self, interaction: discord.Interaction,
                         username: str, email: str, first_name: str, 
                         last_name: str, password: Optional[str] = None):
        """Create a new Pterodactyl user"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        if not user_config.can_create_users:
            await interaction.response.send_message(
                "You don't have permission to create users.",
                ephemeral=True
            )
            return
        
        # Validate email format
        if "@" not in email or "." not in email.split("@")[-1]:
            await interaction.response.send_message(
                "❌ Invalid email format.",
                ephemeral=True
            )
            return
        
        # Generate password if not provided
        if not password:
            password = self.generate_password(12)
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Create user
            new_user = await ptero_client.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            embed = discord.Embed(
                title="✅ User Created Successfully",
                description=f"Created Pterodactyl user: `{username}`",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="User Information",
                value=(
                    f"**Username:** {new_user.username}\n"
                    f"**Email:** {new_user.email}\n"
                    f"**Name:** {new_user.first_name} {new_user.last_name}\n"
                    f"**User ID:** {new_user.id}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="Login Credentials",
                value=(
                    f"**Username:** {new_user.username}\n"
                    f"**Password:** ||{password}||"
                ),
                inline=False
            )
            
            embed.add_field(
                name="⚠️ Important",
                value="Please save these credentials securely. The password is hidden for security.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_create",
                target_type="user",
                target_id=new_user.id,
                details={
                    "username": username,
                    "email": email,
                    "created_by": interaction.user.display_name
                },
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating user: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_create",
                target_type="user",
                success=False,
                error_message=str(e)
            )
    
    @user.command(name="list", description="List all Pterodactyl users")
    async def user_list(self, interaction: discord.Interaction):
        """List all Pterodactyl users"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        if not user_config.can_create_users:
            await interaction.response.send_message(
                "You don't have permission to manage users.",
                ephemeral=True
            )
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            users = await ptero_client.get_users()
            
            if not users:
                embed = discord.Embed(
                    title="👥 No Users Found",
                    description="No users found on your Pterodactyl panel.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="👥 Pterodactyl Users",
                description=f"Found {len(users)} user(s) on your panel",
                color=discord.Color.blue()
            )
            
            for user in users[:15]:  # Limit to 15 users
                admin_badge = "👑" if user.root_admin else ""
                field_value = (
                    f"**ID:** {user.id}\n"
                    f"**Email:** {user.email}\n"
                    f"**Name:** {user.first_name} {user.last_name}\n"
                    f"**Admin:** {'Yes' if user.root_admin else 'No'}"
                )
                
                embed.add_field(
                    name=f"{admin_badge} {user.username}",
                    value=field_value,
                    inline=False
                )
            
            if len(users) > 15:
                embed.set_footer(text=f"Showing 15 of {len(users)} users")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_list",
                target_type="user",
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error fetching users: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_list",
                target_type="user",
                success=False,
                error_message=str(e)
            )
    
    @user.command(name="info", description="Get information about a specific user")
    @app_commands.describe(
        user_identifier="User ID or username"
    )
    async def user_info(self, interaction: discord.Interaction, user_identifier: str):
        """Get detailed information about a specific user"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        if not user_config.can_create_users:
            await interaction.response.send_message(
                "You don't have permission to manage users.",
                ephemeral=True
            )
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Try to find user by ID first, then by username
            target_user = None
            
            # Try as user ID
            try:
                target_user = await ptero_client.get_user(user_identifier)
            except:
                pass
            
            # If not found, try by username
            if not target_user:
                users = await ptero_client.get_users()
                for user in users:
                    if user.username.lower() == user_identifier.lower():
                        target_user = user
                        break
            
            if not target_user:
                await interaction.response.send_message(
                    f"❌ User '{user_identifier}' not found.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"👥 {target_user.username}",
                description=f"User ID: {target_user.id}",
                color=discord.Color.blue()
            )
            
            admin_badge = "👑 " if target_user.root_admin else ""
            embed.add_field(
                name="📋 Basic Information",
                value=(
                    f"**Username:** {admin_badge}{target_user.username}\n"
                    f"**Email:** {target_user.email}\n"
                    f"**Full Name:** {target_user.first_name} {target_user.last_name}\n"
                    f"**Language:** {target_user.language}"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔐 Permissions",
                value=(
                    f"**Root Admin:** {'Yes' if target_user.root_admin else 'No'}\n"
                    f"**Can Access Panel:** Yes"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📅 Account Information",
                value=(
                    f"**Created:** {target_user.created_at}\n"
                    f"**User ID:** {target_user.id}"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_info",
                target_type="user",
                target_id=target_user.id,
                details={"username": target_user.username},
                success=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error fetching user info: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_info",
                target_type="user",
                target_id=user_identifier,
                success=False,
                error_message=str(e)
            )
    
    @user.command(name="update", description="Update an existing user")
    @app_commands.describe(
        user_identifier="User ID or username",
        email="New email address (optional)",
        first_name="New first name (optional)",
        last_name="New last name (optional)",
        password="New password (optional)"
    )
    async def user_update(self, interaction: discord.Interaction,
                         user_identifier: str, email: Optional[str] = None,
                         first_name: Optional[str] = None, 
                         last_name: Optional[str] = None,
                         password: Optional[str] = None):
        """Update an existing Pterodactyl user"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        if not user_config.can_create_users:
            await interaction.response.send_message(
                "You don't have permission to manage users.",
                ephemeral=True
            )
            return
        
        # Validate email if provided
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            await interaction.response.send_message(
                "❌ Invalid email format.",
                ephemeral=True
            )
            return
        
        # Check if at least one field is provided
        if not any([email, first_name, last_name, password]):
            await interaction.response.send_message(
                "❌ Please provide at least one field to update.",
                ephemeral=True
            )
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Find user
            target_user = None
            
            # Try as user ID first
            try:
                target_user = await ptero_client.get_user(user_identifier)
            except:
                pass
            
            # If not found, try by username
            if not target_user:
                users = await ptero_client.get_users()
                for user in users:
                    if user.username.lower() == user_identifier.lower():
                        target_user = user
                        break
            
            if not target_user:
                await interaction.response.send_message(
                    f"❌ User '{user_identifier}' not found.",
                    ephemeral=True
                )
                return
            
            # Prepare update data
            update_data = {}
            if email:
                update_data["email"] = email
            if first_name:
                update_data["first_name"] = first_name
            if last_name:
                update_data["last_name"] = last_name
            if password:
                update_data["password"] = password
            
            # Update user
            success = await ptero_client.update_user(target_user.id, **update_data)
            
            if success:
                embed = discord.Embed(
                    title="✅ User Updated Successfully",
                    description=f"Updated user: `{target_user.username}`",
                    color=discord.Color.green()
                )
                
                # Show updated fields
                updated_fields = []
                if email:
                    updated_fields.append(f"**Email:** {email}")
                if first_name:
                    updated_fields.append(f"**First Name:** {first_name}")
                if last_name:
                    updated_fields.append(f"**Last Name:** {last_name}")
                if password:
                    updated_fields.append("**Password:** [Updated]")
                
                embed.add_field(
                    name="Updated Fields",
                    value="\n".join(updated_fields),
                    inline=False
                )
                
                embed.add_field(
                    name="User Information",
                    value=f"**Username:** {target_user.username}\n**User ID:** {target_user.id}",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="user_update",
                    target_type="user",
                    target_id=target_user.id,
                    details={"username": target_user.username, "updated_fields": list(update_data.keys())},
                    success=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Failed to update user `{target_user.username}`.",
                    ephemeral=True
                )
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="user_update",
                    target_type="user",
                    target_id=target_user.id,
                    success=False,
                    error_message="Update failed"
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error updating user: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_update",
                target_type="user",
                target_id=user_identifier,
                success=False,
                error_message=str(e)
            )
    
    @user.command(name="delete", description="Delete a Pterodactyl user")
    @app_commands.describe(
        user_identifier="User ID or username of the user to delete",
        confirm="Type 'DELETE' to confirm deletion"
    )
    async def user_delete(self, interaction: discord.Interaction,
                         user_identifier: str, confirm: str):
        """Delete a Pterodactyl user"""
        if not await self.bot.check_permissions(interaction):
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        user_config = await self.bot.get_user_config(user_id, guild_id)
        if not user_config:
            return
        
        if not user_config.can_create_users:
            await interaction.response.send_message(
                "You don't have permission to manage users.",
                ephemeral=True
            )
            return
        
        if confirm != "DELETE":
            await interaction.response.send_message(
                "❌ You must type 'DELETE' to confirm user deletion.",
                ephemeral=True
            )
            return
        
        try:
            ptero_client = self.bot.get_ptero_client(user_config)
            
            # Find user
            target_user = None
            
            # Try as user ID first
            try:
                target_user = await ptero_client.get_user(user_identifier)
            except:
                pass
            
            # If not found, try by username
            if not target_user:
                users = await ptero_client.get_users()
                for user in users:
                    if user.username.lower() == user_identifier.lower():
                        target_user = user
                        break
            
            if not target_user:
                await interaction.response.send_message(
                    f"❌ User '{user_identifier}' not found.",
                    ephemeral=True
                )
                return
            
            # Delete user
            success = await ptero_client.delete_user(target_user.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ User Deleted Successfully",
                    description=f"Deleted user: `{target_user.username}`",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="Deleted User Information",
                    value=(
                        f"**Username:** {target_user.username}\n"
                        f"**Email:** {target_user.email}\n"
                        f"**User ID:** {target_user.id}"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="⚠️ Warning",
                    value="This action cannot be undone. All servers owned by this user may be affected.",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="user_delete",
                    target_type="user",
                    target_id=target_user.id,
                    details={"username": target_user.username, "email": target_user.email},
                    success=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Failed to delete user `{target_user.username}`.",
                    ephemeral=True
                )
                
                await self.bot.create_audit_log(
                    discord_user_id=user_id,
                    guild_id=guild_id,
                    action="user_delete",
                    target_type="user",
                    target_id=target_user.id,
                    success=False,
                    error_message="Deletion failed"
                )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error deleting user: {str(e)}",
                ephemeral=True
            )
            await self.bot.create_audit_log(
                discord_user_id=user_id,
                guild_id=guild_id,
                action="user_delete",
                target_type="user",
                target_id=user_identifier,
                success=False,
                error_message=str(e)
            )
    
    def generate_password(self, length: int = 12) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
