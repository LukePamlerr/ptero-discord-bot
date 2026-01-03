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

## 🥚 Pterodactyl Panel Deployment

### 📋 Deploying on Your Existing Pterodactyl Panel

If you already have a Pterodactyl panel, you can easily deploy the Discord bot using the built-in Python egg. This keeps everything in one place and leverages your existing infrastructure.

#### 🚀 Quick Setup Guide

**Step 1: Create a New Nest**
1. Login to your Pterodactyl admin panel
2. Navigate to **Admin → Nests**
3. Click **Create New Nest**
4. **Name:** `Discord Bot`
5. **Description:** `Pterodactyl Discord Bot for server management`
6. **Docker Image:** `python:3.11-slim`

**Step 2: Create the Egg**
1. In your new nest, click **Create New Egg**
2. **Name:** `Pterodactyl Discord Bot`
3. **Description:** `Advanced Discord bot for Pterodactyl panel management`
4. **Docker Image:** `ghcr.io/pterodactyl/yolks:python_3.11`
5. **Startup Command:** `python bot.py`

**Step 3: Configure Egg Variables**
Add these environment variables to your egg:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DISCORD_BOT_TOKEN` | Discord bot token from Developer Portal | - | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://username:password@localhost:5432/ptero_bot` | ✅ |
| `DISCORD_GUILD_ID` | Discord server ID (optional) | - | ❌ |
| `BOT_PREFIX` | Command prefix | `!` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `ENABLE_WEB_INTERFACE` | Enable web interface | `true` | ❌ |
| `WEB_PORT` | Web interface port | `8080` | ❌ |
| `ENABLE_MONITORING` | Enable monitoring | `true` | ❌ |
| `MAX_SERVERS_PER_USER` | Server limit per user | `10` | ❌ |

**Step 4: Upload Bot Files**
1. Download the bot source code from GitHub
2. **Required files to upload:**
   - `bot.py` (main entry point)
   - `requirements.txt` (Python dependencies)
   - `bot/` directory (all bot modules)
   - `alembic.ini` (database migrations)
   - `alembic/` directory (migration files)

3. Upload these files through the Pterodactyl file manager or SFTP

**Step 5: Create and Configure Server**
1. Navigate to **Servers → Create New Server**
2. Select your "Discord Bot" nest and egg
3. **Server Settings:**
   - **Name:** `Pterodactyl Discord Bot`
   - **Memory:** 1024MB (minimum), 2048MB (recommended)
   - **CPU:** 1 core (minimum), 2 cores (recommended)
   - **Disk:** 2GB (minimum), 4GB (recommended)
   - **Database:** Create a new PostgreSQL database

4. **Set Environment Variables:**
   - `DISCORD_BOT_TOKEN`: Your Discord bot token
   - `DATABASE_URL`: Your Pterodactyl database connection string
   - `DISCORD_GUILD_ID`: Your Discord server ID (optional)

**Step 6: Start the Bot**
1. Click **Start Server**
2. Monitor the console for startup logs
3. The bot will automatically connect to Discord and register commands

#### 🔧 Database Setup

**Option 1: Use Pterodactyl's Built-in Database**
```sql
-- Database will be automatically created by Pterodactyl
-- Just use the connection string provided in the server settings
```

**Option 2: External Database**
```bash
# Create database manually
CREATE DATABASE ptero_bot;
CREATE USER ptero_bot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ptero_bot TO ptero_bot_user;
```

**Run Database Migrations:**
```bash
# SSH into your server or use the Pterodactyl console
python -m alembic upgrade head
```

#### 🎯 Discord Bot Setup

**Create Discord Application:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Add a bot to the application
4. Enable **Server Members Intent** and **Message Content Intent**
5. Copy the **Bot Token**

**Invite Bot to Server:**
1. Generate OAuth2 URL with permissions:
   - `applications.commands`
   - `bot`
   - `administrator` (recommended)
2. Invite the bot to your Discord server

#### 📊 Monitoring and Management

**Pterodactyl Integration:**
- **Console Logs:** View bot logs through Pterodactyl console
- **Resource Monitoring:** Monitor CPU, memory, and disk usage
- **Auto-restart:** Bot automatically restarts if it crashes
- **Backups:** Use Pterodactyl's backup system for bot data

**Web Interface:**
- Access the bot's web interface at `http://your-server-ip:8080`
- Configure settings and view analytics
- Manage users and permissions

#### 🔒 Security Best Practices

**Environment Variables:**
- Never commit Discord tokens to git
- Use strong database passwords
- Rotate API keys regularly

**Network Security:**
- Use Pterodactyl's built-in firewall
- Limit database access to the bot server only
- Enable SSL/TLS for web interface

**User Permissions:**
- Use Discord role-based permissions
- Limit bot commands to authorized users
- Enable audit logging

#### 🐛 Troubleshooting

**Common Issues:**

1. **Bot Won't Start**
   - Check environment variables are set correctly
   - Verify Discord bot token is valid
   - Check database connection string

2. **Commands Not Working**
   - Ensure bot has proper Discord permissions
   - Check if commands are registered (wait 1-2 minutes after startup)
   - Verify user has configured their Pterodactyl panel

3. **Database Connection Failed**
   - Check database is running and accessible
   - Verify connection string format
   - Ensure database user has proper permissions

4. **Performance Issues**
   - Increase server memory allocation
   - Check resource usage in Pterodactyl
   - Enable debug logging to identify bottlenecks

**Debug Mode:**
```bash
# Enable debug logging through environment variable
LOG_LEVEL=DEBUG
```

#### 🎉 Benefits of Pterodactyl Deployment

✅ **Unified Management:** Everything in one control panel
✅ **Resource Efficiency:** Shared infrastructure
✅ **Auto-scaling:** Dynamic resource allocation
✅ **Built-in Monitoring:** Pterodactyl metrics and alerts
✅ **Easy Backups:** Integrated backup system
✅ **SSL/TLS:** Automatic certificate management
✅ **Security:** Isolated container environment
✅ **Cost Effective:** No additional hosting costs

#### 📚 Advanced Configuration

**Custom Domain Setup:**
```nginx
# Add to your Pterodactyl nginx configuration
server {
    listen 80;
    server_name bot.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Performance Optimization:**
- Increase memory for large Discord servers
- Enable Redis for caching (if available)
- Use SSD storage for better performance
- Monitor resource usage regularly

---

## 🚀 Deployment Options

### 🐳 Docker Deployment

**📦 Quick Start with Docker Compose:**
```bash
# Build the image
docker build -t ptero-discord-bot .

# Run with environment variables
docker run -d \
  --name ptero-discord-bot \
  -e DISCORD_BOT_TOKEN="your_token_here" \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e DISCORD_GUILD_ID="your_guild_id" \
  ptero-discord-bot
```

### ☸️ Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ptero-discord-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ptero-discord-bot
  template:
    metadata:
      labels:
        app: ptero-discord-bot
    spec:
      containers:
      - name: bot
        image: ptero-discord-bot:latest
        env:
        - name: DISCORD_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: discord-token
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: database-url
```

### 🌐 Cloud Platform Deployment

**🟣 Heroku:**
```bash
# Install Heroku CLI and login
heroku create ptero-discord-bot
heroku config:set DISCORD_BOT_TOKEN="your_token"
heroku config:set DATABASE_URL="your_database_url"
git push heroku main
```

**🔵 DigitalOcean:**
```bash
# Create droplet and deploy
doctl compute droplet create ptero-bot \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-4gb \
  --region nyc1
```

**🟠 AWS ECS:**
```bash
# Push to ECR and deploy
aws ecr get-login-password | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker tag ptero-discord-bot:latest <account-id>.dkr.ecr.<region>.amazonaws.com/ptero-discord-bot:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/ptero-discord-bot:latest
```

## 📋 Configuration Management

### 🔑 Environment Variables

**Required Variables:**
- `DISCORD_BOT_TOKEN` - Discord bot token from Developer Portal
- `DATABASE_URL` - PostgreSQL connection string
- `DISCORD_GUILD_ID` - Discord server ID (optional, for guild-specific commands)

**Optional Variables:**
- `BOT_PREFIX` - Command prefix (default: `!`)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_SERVERS_PER_USER` - Server limit per user (default: 10)
- `ENABLE_WEB_INTERFACE` - Enable web interface (default: true)
- `WEB_PORT` - Web interface port (default: 8080)
- `AUTO_BACKUP_INTERVAL` - Backup interval in hours (default: 24)
- `ENABLE_MONITORING` - Enable monitoring (default: true)
- `ALERT_THRESHOLD_CPU` - CPU alert threshold (default: 80)
- `ALERT_THRESHOLD_MEMORY` - Memory alert threshold (default: 85)

### 🗄️ Database Setup

**PostgreSQL Configuration:**
```sql
-- Create database
CREATE DATABASE ptero_bot;

-- Create user
CREATE USER ptero_bot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ptero_bot TO ptero_bot_user;
```

**Run Database Migrations:**
```bash
# Initialize database
python scripts/setup_database.py

# Run migrations
alembic upgrade head
```

## 🛠️ Available Commands

### 🖥️ Server Commands
- `/server list` - List all accessible servers
- `/server status <server>` - View server status and resources
- `/server start <server>` - Start a server
- `/server stop <server>` - Stop a server
- `/server restart <server>` - Restart a server
- `/server kill <server>` - Force kill a server
- `/server command <server> <command>` - Send console command

### 👥 User Commands
- `/user create <email> <username>` - Create new user
- `/user list` - List all users
- `/user info <user>` - View user details
- `/user update <user> <field> <value>` - Update user
- `/user delete <user>` - Delete user

### 📊 Monitoring Commands
- `/monitor status <server>` - Real-time monitoring
- `/monitor alerts` - View active alerts
- `/monitor history <server>` - View historical data
- `/monitor set_threshold <type> <value>` - Set alert thresholds

### 💾 Backup Commands
- `/backup create <server>` - Create backup
- `/backup list` - List all backups
- `/backup restore <backup>` - Restore backup
- `/backup delete <backup>` - Delete backup

### 📈 Analytics Commands
- `/analytics overview` - Server overview
- `/analytics usage <server>` - Usage statistics
- `/analytics compare <server1> <server2>` - Compare servers
- `/analytics report <format>` - Generate report

### 🔔 Notification Commands
- `/notification setup <webhook>` - Setup notifications
- `/notification test` - Test notifications
- `/notification disable` - Disable notifications

### ⚙️ Schedule Commands
- `/schedule create <name> <cron> <action>` - Create schedule
- `/schedule list` - List schedules
- `/schedule delete <schedule>` - Delete schedule

### 🛠️ Utility Commands
- `/utility ping` - Check bot latency
- `/utility health` - System health check
- `/utility search <query>` - Search servers/users
- `/utility export <format>` - Export data
- `/utility import <data>` - Import data
- `/utility cleanup` - Cleanup old data
- `/utility generate <type>` - Generate passwords/tokens

### 🔐 Admin Commands
- `/admin config` - View guild configuration
- `/admin permissions <user> <role>` - Manage permissions
- `/admin audit` - View audit logs
- `/admin reset <user>` - Reset user configuration

## 🔒 Security Features

### 🛡️ Encryption & Security
- **Fernet encryption** for sensitive data storage
- **API key rotation** support
- **Role-based permissions** with granular controls
- **Comprehensive audit logging** for all actions
- **Secure credential management** with environment variables

### 👥 Access Control
- **Per-user configuration** isolation
- **Guild-based permissions** system
- **Admin-only commands** protection
- **User role verification** before actions

## 🐛 Troubleshooting

### 🔧 Common Issues

**Bot Not Responding:**
- Check Discord bot token is valid
- Verify bot has proper permissions
- Ensure database connection is working

**Database Connection Errors:**
- Verify DATABASE_URL format
- Check PostgreSQL service status
- Ensure proper database permissions

**Pterodactyl API Errors:**
- Verify API key permissions
- Check panel URL accessibility
- Ensure user has server access

**Memory Issues:**
- Increase server memory allocation
- Check for memory leaks in bot
- Monitor resource usage

### 📝 Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python bot.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Discord Server:** [Join our community](https://discord.gg/your-server)
- **GitHub Issues:** [Report bugs](https://github.com/your-repo/issues)
- **Documentation:** [Full docs](https://your-docs-site.com)

## 🎯 Roadmap

- [ ] Web dashboard for bot management
- [ ] Mobile app for server management
- [ ] Advanced analytics dashboard
- [ ] Multi-panel support
- [ ] Plugin system for custom commands

---

**Made with ❤️ for the Pterodactyl community**