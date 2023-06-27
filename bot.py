import logging
import os
from datetime import datetime

import disnake
from disnake.ext import commands

import database
from config import Config


# Logging configuration
log_format = '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
logfilename = (f'logs/bot_{str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))}.log')
logging.basicConfig(level=Config.log_level, format=log_format, datefmt=date_format)
logger = logging.getLogger(__name__)
logger.setLevel(Config.log_level)

try:
    os.makedirs('logs', exist_ok=True)
    logger.info('logs directory created successfully')
except OSError:
    logger.info('logs directory could not be created')

handler = logging.FileHandler(filename=logfilename, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
logger.addHandler(handler)


# Use prefixes from environment variable or use fallback
# Will no longer be needed after switching to slash commands
def get_prefix(client, message):
    return commands.when_mentioned_or(*Config.discord_bot_prefixes)(client, message)


def get_intents():
    bot_intents = disnake.Intents.default()
    bot_intents.message_content = True
    return bot_intents


class JamalBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            intents=get_intents(),
            command_prefix=get_prefix
        )

    async def on_ready(self) -> None:
        logger.info(f'disnake version: {disnake.__version__}')
        logger.info(f'Logged in as: {bot.user} - {bot.user.id}')
        activity = disnake.Game(name=Config.discord_bot_activity)
        await bot.change_presence(
            status=disnake.Status.online,
            activity=activity)
        # Logging done lets Pterodactyl know that it's ready
        logger.info('Done')

    def add_cog(self, cog: commands.Cog, *, override: bool = False) -> None:
        logger.info(f'Loading cog {cog.qualified_name}')
        return super().add_cog(cog, override=override)


if __name__ == '__main__':
    # Only creates the database if it doesn't exist
    database.create_db('quotes.db')

    bot = JamalBot()
    bot.load_extensions(os.path.join(Config.cogs_folder))
    bot.run(Config.discord_api_key)
