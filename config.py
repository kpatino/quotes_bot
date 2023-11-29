# SPDX-FileCopyrightText: 2023 Kevin Patino
# SPDX-License-Identifier: MIT

from environs import Env


class Config:
    env = Env()
    env.read_env()

    cogs_folder = env.str("COGS_FOLDER", "./cogs/")
    discord_admin_role_id = env.int("DISCORD_ADMIN_ROLE_ID")
    discord_api_key = env("DISCORD_API_KEY")
    discord_mod_role_id = env.int("DISCORD_MOD_ROLE_ID")
    discord_bot_activity = env.str("DISCORD_BOT_ACTIVITY", "Warframe")
    discord_bot_prefixes = env.list("DISCORD_BOT_PREFIXES", '.')
    default_server_address = env("DEFAULT_SERVER_ADDRESS")
    log_level = env.log_level("LOG_LEVEL", 'INFO')
    timezone_list = env.list("TIMEZONE_LIST", 'Europe/London,US/Pacific')
