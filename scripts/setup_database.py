#!/usr/bin/env python3
"""
Database setup script for Pterodactyl Discord Bot
This script creates the initial database migration and sets up the database schema.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def main():
    """Setup the database with initial migration"""
    print("🔧 Setting up Pterodactyl Discord Bot Database...")
    
    # Check environment variables
    required_env_vars = ['DATABASE_URL']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set up your .env file with the required variables.")
        return False
    
    # Create initial migration
    print("📝 Creating initial migration...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'revision', '--autogenerate', '-m', 'Initial migration'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode != 0:
            print(f"❌ Error creating migration: {result.stderr}")
            return False
        
        print("✅ Initial migration created successfully")
    except Exception as e:
        print(f"❌ Error creating migration: {str(e)}")
        return False
    
    # Apply migration
    print("🔄 Applying database migration...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'alembic', 'upgrade', 'head'
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode != 0:
            print(f"❌ Error applying migration: {result.stderr}")
            return False
        
        print("✅ Database migration applied successfully")
    except Exception as e:
        print(f"❌ Error applying migration: {str(e)}")
        return False
    
    print("🎉 Database setup complete!")
    print("\nNext steps:")
    print("1. Configure your Discord bot token in .env")
    print("2. Run the bot with: python bot.py")
    print("3. Use /setup in your Discord server to configure the bot")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
