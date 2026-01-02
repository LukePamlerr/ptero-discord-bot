# Pterodactyl Discord Bot

A powerful Discord bot for managing Pterodactyl game server panels directly from Discord. This bot allows users to start, stop, restart servers, send console commands, and manage users through intuitive slash commands with advanced monitoring, analytics, and self-hosting capabilities.

## 🌟 Features

### 🖥️ Server Management
- **Start/Stop/Restart/Kill servers** with simple slash commands
- **View server status** and real-time resource usage (CPU, Memory, Disk)
- **Send console commands** to running servers
- **List all accessible servers** with detailed information
- **Server performance monitoring** with historical data
- **Automated backup creation and restoration**

### 👥 User Management
- **Create new Pterodactyl users** with automatic password generation
- **List and view user information** with role management
- **Update existing users** (email, name, password, permissions)
- **Delete users** with confirmation and audit logging
- **Bulk user operations** for efficient management

### 📊 Monitoring & Analytics
- **Real-time resource monitoring** (CPU, Memory, Disk, Network)
- **Performance analytics** with historical trends
- **Server comparison tools** for optimization
- **Custom alerts** and threshold management
- **Automated reporting** in multiple formats (JSON, CSV, Text)

### 🔔 Notifications & Automation
- **Discord notifications** for server events
- **Custom alert thresholds** for resource usage
- **Scheduled tasks** and automation rules
- **Webhook integrations** for external services
- **Alert history** and management

### 💾 Backup Management
- **Automated backup creation** with scheduling
- **Backup restoration** with confirmation dialogs
- **Backup history** and metadata management
- **Cross-server backup** operations
- **Backup compression** and optimization

### 🔐 Security & Configuration
- **Encrypted credential storage** using Fernet encryption
- **Per-user configuration** with panel URL and API keys
- **Role-based permissions** for granular access control
- **Comprehensive audit logging** for all actions
- **API key rotation** and security management

### 🛡️ Admin Features
- **Guild configuration** and role management
- **User permission management** with detailed controls
- **Audit log viewing** with advanced filtering
- **User configuration reset** capabilities
- **System health monitoring** and diagnostics

### 🛠️ Utility Tools
- **System health checks** and diagnostics
- **Search functionality** for servers and users
- **Data import/export** for configuration management
- **Secure password/token generation**
- **Cleanup tools** for optimization

## Self-Hosting on Pterodactyl Panel

### 🥚 Deploying the Bot on Your Pterodactyl Panel

You can deploy this Discord bot directly on your Pterodactyl panel using a custom egg. This eliminates the need for separate hosting and keeps everything in one place.

#### Quick Deployment Option

**🚀 Automated Deployment Script:**
```bash
# Run our automated deployment tool
python scripts/deploy_pterodactyl.py
```

This script will automatically:
- ✅ Create the Discord Bot nest
- ✅ Create the custom egg configuration  
- ✅ Upload all necessary files
- ✅ Generate deployment scripts
- ✅ Provide step-by-step instructions

#### Manual Deployment Steps

If you prefer manual setup, follow these steps:

1. **Navigate to Admin → Nests → Create New Nest**
   - **Name:** Discord Bot
   - **Description:** Pterodactyl Discord Bot for server management
   - **Docker Image:** `python:3.11-slim`

2. **Create a New Egg in the Nest**
   ```json
   {
     "name": "Pterodactyl Discord Bot",
     "description": "Advanced Discord bot for Pterodactyl#### 🐳 Docker Deployment

**Using Docker Compose (Recommended):**
   - Use Pterodactyl's built-in database or external
   - Create database: `ptero_bot`
   - Update connection string accordingly

2. **Run Database Migrations**
   ```bash
   # SSH into your server
   python scripts/setup_database.py
   ```

#### Benefits of Self-Hosting

✅ **Advantages:**
- **Single Platform:** Everything runs on your Pterodactyl panel
- **Resource Efficiency:** Shared resources with existing infrastructure
- **Simplified Management:** One control panel for everything
- **Cost Effective:** No additional hosting costs
- **Integrated Monitoring:** Use Pterodactyl's built-in metrics
- **Auto-scaling:** Leverage Pterodactyl's resource management

✅ **Features Available:**
- All Discord bot functionality
- Web interface for configuration
- Automatic restarts on crashes
- Resource monitoring through Pterodactyl
- Backup integration with Pterodactyl's system
- SSL termination through Pterodactyl

#### Advanced Configuration

##### Custom Domain Setup
```nginx
server {
    listen 80;
    server_name your-bot-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

##### SSL Certificate
- Use Pterodactyl's built-in SSL
- Or upload custom certificates
- Automatic renewal available

##### Performance Optimization
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 bot
USER bot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

EXPOSE 8080

CMD ["python", "bot.py"]
```

#### Monitoring and Logging

##### Pterodactyl Integration
- **Logs:** View through Pterodactyl console
- **Metrics:** Use Pterodactyl's resource graphs
- **Alerts:** Configure through Pterodactyl alerts
- **Backups:** Leverage Pterodactyl's backup system

##### Custom Monitoring
```python
# Add to bot.py for health endpoint
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

#### Troubleshooting Self-Hosting

##### Common Issues

1. **Bot Won't Start**
   - Check environment variables
   - Verify database connection
   - Review Pterodactyl console logs

2. **Database Connection Failed**
   - Ensure PostgreSQL is running
   - Check connection string format
   - Verify firewall settings

3. **Discord Connection Issues**
   - Validate bot token
   - Check Discord API status
   - Verify guild permissions

4. **Performance Issues**
   - Increase allocated resources
   - Optimize database queries
   - Enable caching

##### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
python bot.py
```

#### Security Considerations

✅ **Best Practices:**
- **Environment Variables:** Never commit tokens to git
- **Database Security:** Use strong passwords
- **Network Security:** Configure firewall rules
- **SSL:** Always use HTTPS
- **Updates:** Keep dependencies updated

✅ **Access Control:**
- **Bot Permissions:** Principle of least privilege
- **Database Access:** Restricted IPs only
- **Admin Access:** Multi-factor authentication
- **API Keys:** Regular rotation

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