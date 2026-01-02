# Pterodactyl Discord Bot

A powerful Discord bot for managing Pterodactyl game server panels directly from Discord. This bot allows users to start, stop, restart servers, send console commands, and manage users through intuitive slash commands.

## Features

### 🖥️ Server Management
- **Start/Stop/Restart/Kill servers** with simple slash commands
- **View server status** and resource usage (CPU, Memory, Disk)
- **Send console commands** to running servers
- **List all accessible servers** with detailed information

### 👥 User Management
- **Create new Pterodactyl users** with automatic password generation
- **List and view user information**
- **Update existing users** (email, name, password)
- **Delete users** (with confirmation)

### 🔐 Security & Configuration
- **Encrypted credential storage** using Fernet encryption
- **Per-user configuration** with panel URL and API keys
- **Role-based permissions** for server and user management
- **Comprehensive audit logging** for all actions

### 🛡️ Admin Features
- **Guild configuration** and role management
- **User permission management**
- **Audit log viewing** and filtering
- **User configuration reset** capabilities

## Quick Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Pterodactyl panel with Application API access
- Discord bot token

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ptero-discord-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   DISCORD_CLIENT_ID=your_discord_client_id_here
   DISCORD_GUILD_ID=your_discord_guild_id_here
   DATABASE_URL=postgresql://username:password@localhost:5432/ptero_bot
   PTERODACTYL_PANEL_URL=your_ptero_panel_url_here
   PTERODACTYL_API_KEY=your_ptero_api_key_here
   ```

4. **Create database**
   ```sql
   CREATE DATABASE ptero_bot;
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

### Discord Bot Setup

1. **Create a Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Add a bot to the application

2. **Configure Bot Permissions**
   - Enable Server Members Intent
   - Enable Message Content Intent
   - Copy the bot token

3. **Invite Bot to Server**
   - Generate an OAuth2 URL with these permissions:
     - `applications.commands`
     - `bot`
     - `administrator` (recommended for full functionality)

## Usage

### Initial Setup (Server Admin)
1. Use `/setup` to configure the bot for your server
2. Set an admin role (optional, defaults to server administrators)

### User Configuration
Each user must configure their own Pterodactyl panel:

```
/config setup panel_url:https://panel.example.com api_key:your_api_key
```

### Server Commands
```
/server list                    # List all your servers
/server info server_identifier  # Get detailed server info
/server start server_identifier # Start a server
/server stop server_identifier  # Stop a server
/server restart server_identifier # Restart a server
/server kill server_identifier  # Force kill a server
/server command server_identifier "say Hello World" # Send console command
```

### User Management Commands
```
/user create username email first_name last_name [password]  # Create user
/user list                    # List all users
/user info user_identifier    # Get user information
/user update user_identifier [email] [first_name] [last_name] [password]  # Update user
/user delete user_identifier DELETE  # Delete user (requires confirmation)
```

### Admin Commands
```
/admin status                 # Bot status and statistics
/admin users                  # List configured users
/admin audit [limit] [user_id] [action]  # View audit logs
/admin permissions @user [can_manage_servers] [can_create_users] [max_servers]  # Modify permissions
/admin reset @user RESET      # Reset user configuration
```

## Security Features

### Encryption
- All sensitive data (panel URLs, API keys) are encrypted using Fernet symmetric encryption
- Encryption keys are stored securely in environment variables
- Database contains only encrypted sensitive information

### Permissions
- Role-based access control
- Per-user permission settings
- Audit logging for all actions

### API Security
- Validates Pterodactyl API credentials during setup
- Secure HTTP requests with proper error handling
- No credential exposure in logs or responses

## Database Schema

The bot uses PostgreSQL with the following main tables:
- `guild_configs` - Server-specific settings
- `user_configs` - User Pterodactyl configurations (encrypted)
- `server_configs` - Linked server information
- `audit_logs` - Action logging and tracking

## Pterodactyl API Integration

The bot integrates with the Pterodactyl Application API to provide:
- Server power management (start/stop/restart/kill)
- Resource monitoring (CPU, memory, disk usage)
- Console command execution
- User management operations
- Server and user information retrieval

## Troubleshooting

### Common Issues

1. **Bot won't start**
   - Check environment variables are set correctly
   - Verify database connection string
   - Ensure Discord bot token is valid

2. **API connection fails**
   - Verify Pterodactyl panel URL is accessible
   - Check API key has Application API permissions
   - Ensure API key is not expired

3. **Commands not working**
   - Verify bot has proper Discord permissions
   - Check user has configured their panel
   - Review audit logs for error details

### Debug Mode
Enable debug logging by setting the log level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the audit logs for detailed error information