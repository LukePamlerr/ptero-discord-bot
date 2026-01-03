#!/usr/bin/env python3
"""
Pterodactyl Discord Bot - Main Entry Point

A powerful Discord bot for managing Pterodactyl game server panels directly from Discord.
This bot provides server management, user administration, monitoring, analytics, and automation
capabilities through intuitive slash commands.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.core import PteroBot

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the bot"""
    try:
        # Validate required environment variables
        required_vars = ['DISCORD_BOT_TOKEN', 'DATABASE_URL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please set these variables in your .env file or environment")
            sys.exit(1)
        
        # Create and run the bot
        logger.info("Starting Pterodactyl Discord Bot...")
        bot = PteroBot()
        
        # Run the bot with the Discord token
        bot.run(os.getenv('DISCORD_BOT_TOKEN'))
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
