#!/usr/bin/env python3
"""
Pterodactyl Deployment Script
Automates the deployment of the Discord bot to a Pterodactyl panel
"""

import os
import sys
import json
import requests
from pathlib import Path

class PterodactylDeployer:
    """Handles deployment to Pterodactyl panel"""
    
    def __init__(self, panel_url, api_key):
        self.panel_url = panel_url.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.panel_url}/api/application"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def create_nest(self):
        """Create the Discord Bot nest"""
        nest_data = {
            "name": "Discord Bot",
            "description": "Advanced Discord bot for Pterodactyl panel management",
            "docker_images": {
                "ghcr.io/pterodactyl/yolks:python_3.11": "Python 3.11 Slim"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/nests",
            json=nest_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            return response.json()["data"]["attributes"]
        else:
            print(f"❌ Failed to create nest: {response.text}")
            return None
    
    def create_egg(self, nest_id):
        """Create the Discord Bot egg"""
        egg_config = {
            "name": "Pterodactyl Discord Bot",
            "description": "Advanced Discord bot for Pterodactyl panel management with server control, user management, monitoring, and analytics",
            "startup": "python bot.py",
            "image": "ghcr.io/pterodactyl/yolks:python_3.11",
            "config": {
                "files": {
                    "bot.py": {
                        "parser": "file"
                    }
                },
                "startup": {
                    "done": "Server is ready to accept connections",
                    "user": "You can now use Discord commands to manage your Pterodactyl panel"
                },
                "logs": {
                    "custom": True,
                    "location": "logs/"
                }
            },
            "variables": [
                {
                    "name": "Discord Bot Token",
                    "description": "Your Discord application bot token from the Developer Portal",
                    "env_variable": "DISCORD_BOT_TOKEN",
                    "default_value": "",
                    "user_viewable": True,
                    "user_editable": True,
                    "rules": "required|string|max:128"
                },
                {
                    "name": "Database URL",
                    "description": "PostgreSQL database connection string for the bot",
                    "env_variable": "DATABASE_URL",
                    "default_value": "postgresql://username:password@localhost:5432/ptero_bot",
                    "user_viewable": True,
                    "user_editable": True,
                    "rules": "required|string|max:256"
                },
                {
                    "name": "Discord Guild ID",
                    "description": "Optional: Specific Discord server ID for command registration",
                    "env_variable": "DISCORD_GUILD_ID",
                    "default_value": "",
                    "user_viewable": True,
                    "user_editable": True,
                    "rules": "nullable|string|max:20"
                }
            ]
        }
        
        response = requests.post(
            f"{self.base_url}/nests/{nest_id}/eggs",
            json=egg_config,
            headers=self.headers
        )
        
        if response.status_code == 201:
            return response.json()["data"]["attributes"]
        else:
            print(f"❌ Failed to create egg: {response.text}")
            return None
    
    def upload_files(self, egg_id):
        """Upload bot files to the egg"""
        files_to_upload = [
            "bot.py",
            "requirements.txt",
            "README.md",
            "alembic.ini",
            "scripts/setup_database.py"
        ]
        
        for filename in files_to_upload:
            if Path(filename).exists():
                self._upload_file(egg_id, filename)
            else:
                print(f"⚠️ File not found: {filename}")
    
    def _upload_file(self, egg_id, filename):
        """Upload a single file to the egg"""
        with open(filename, 'rb') as f:
            files = {
                'file': (filename, f, 'application/octet-stream')
            }
            
            response = requests.post(
                f"{self.base_url}/nests/eggs/{egg_id}/files",
                files=files,
                headers=self.headers
            )
            
            if response.status_code == 200:
                print(f"✅ Uploaded: {filename}")
            else:
                print(f"❌ Failed to upload {filename}: {response.text}")
    
    def create_server_script(self, egg_id, nest_id):
        """Create a server script for easy deployment"""
        script_content = f"""#!/bin/bash

# Pterodactyl Discord Bot Auto-Deploy Script
# Generated by deployment tool

set -e

echo "🚀 Deploying Pterodactyl Discord Bot..."

# Check if server already exists
SERVER_NAME="Discord Bot Server"
if [ ! -z "$SERVER_NAME" ]; then
    echo "📝 Creating server: $SERVER_NAME"
    
    # Create server via API
    curl -X POST "{self.base_url}/servers" \\
        -H "Authorization: Bearer {self.api_key}" \\
        -H "Content-Type: application/json" \\
        -d '{{
            "name": "$SERVER_NAME",
            "description": "Discord bot for Pterodactyl management",
            "user": 1,
            "egg": {egg_id},
            "docker_image": "ghcr.io/pterodactyl/yolks:python_3.11",
            "startup": "python bot.py",
            "environment": {{
                "DISCORD_BOT_TOKEN": "$DISCORD_BOT_TOKEN",
                "DATABASE_URL": "$DATABASE_URL",
                "DISCORD_GUILD_ID": "$DISCORD_GUILD_ID"
            }},
            "limits": {{
                "memory": 2048,
                "swap": 0,
                "disk": 4096,
                "io": 500,
                "cpu": 200
            }},
            "feature_limits": {{
                "databases": 2,
                "allocations": 5,
                "backups": 10
            }},
            "deploy": {{
                "locations": [1],
                "dedicated_ip": false,
                "port_range": []
            }}
        }}'
    
    if [ $? -eq 0 ]; then
        echo "✅ Server created successfully!"
        echo "🔧 Configure environment variables in the Pterodactyl panel"
        echo "📊 Monitor deployment in the Pterodactyl console"
    else
        echo "❌ Failed to create server"
        exit 1
    fi
else
    echo "ℹ️ Server already exists or name not set"
fi
"""
        
        script_name = "deploy_discord_bot.sh"
        with open(script_name, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_name, 0o755)
        print(f"✅ Created deployment script: {script_name}")
        
        return script_name

def main():
    """Main deployment function"""
    print("🥚 Pterodactyl Discord Bot Deployment Tool")
    print("=" * 50)
    
    # Get panel credentials
    panel_url = input("🔗 Enter your Pterodactyl panel URL: ").strip()
    if not panel_url.startswith(('http://', 'https://')):
        panel_url = f"https://{panel_url}"
    
    api_key = input("🔑 Enter your Pterodactyl Application API key: ").strip()
    
    # Initialize deployer
    deployer = PterodactylDeployer(panel_url, api_key)
    
    # Test connection
    print("\n🔍 Testing API connection...")
    try:
        response = requests.get(f"{deployer.base_url}/users", headers=deployer.headers)
        if response.status_code == 200:
            print("✅ API connection successful!")
        else:
            print(f"❌ API connection failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return
    
    # Create nest
    print("\n📦 Creating Discord Bot nest...")
    nest = deployer.create_nest()
    if not nest:
        print("❌ Failed to create nest")
        return
    
    nest_id = nest["id"]
    print(f"✅ Nest created with ID: {nest_id}")
    
    # Create egg
    print(f"\n🥚 Creating Discord Bot egg...")
    egg = deployer.create_egg(nest_id)
    if not egg:
        print("❌ Failed to create egg")
        return
    
    egg_id = egg["id"]
    print(f"✅ Egg created with ID: {egg_id}")
    
    # Upload files
    print(f"\n📤 Uploading bot files...")
    deployer.upload_files(egg_id)
    
    # Create deployment script
    print(f"\n📝 Creating deployment script...")
    script_name = deployer.create_server_script(egg_id, nest_id)
    
    print("\n" + "=" * 50)
    print("🎉 Deployment completed successfully!")
    print("\n📋 Next Steps:")
    print(f"1. Upload {script_name} to your server")
    print("2. Make it executable: chmod +x deploy_discord_bot.sh")
    print("3. Run the script: ./deploy_discord_bot.sh")
    print("4. Configure environment variables in Pterodactyl panel")
    print("5. Start the server")
    print("\n🔗 Panel URL:", panel_url)
    print("📚 Documentation: Check README.md for detailed setup instructions")

if __name__ == "__main__":
    main()
