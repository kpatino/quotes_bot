# SPDX-FileCopyrightText: 2023 Kevin Patino
# SPDX-License-Identifier: MIT

import logging
from datetime import datetime

import disnake
import pytz
from disnake.ext import commands

from config import Config

module_logger = logging.getLogger(f'__main__.{__name__}')


async def timezone_embed() -> disnake.Embed:
    """
    Create an embed with the current time in different timezones and return it.

    Returns
        embed: Time in different timezones
    """

    embed = disnake.Embed(title='Time')

    if Config.timezone_list:
        module_logger.debug(f'Using the following timezones: {Config.timezone_list}')
        embed.set_default_colour(disnake.Colour.purple())
        for tz in Config.timezone_list:
            embed.add_field(
                name=tz,
                value=datetime.now(
                    pytz.timezone(tz)).strftime('%b %d %I:%M %p (%H:%M)'),
                inline=False)
    else:
        module_logger.warning('No timezones listed in .env or in an environment variable')
        embed.set_default_colour(disnake.Colour.red())
        embed.add_field(
                name='N/A',
                value='Timezones were not provided in the config',
                inline=False)

    return embed


class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name='time', description='Get the current time in different timezones')
    async def time(self, ctx) -> None:
        module_logger.info(f'Message command "time" executed by {ctx.author.id}')
        await ctx.reply(embed=await timezone_embed(), mention_author=False)

    @commands.slash_command(name='time', description='Get the current time in different timezones')
    async def slash_time(self, inter: disnake.CommandInteraction) -> None:
        module_logger.info(f'Slash command "time" executed by {inter.author.id}')
        await inter.response.send_message(embed=await timezone_embed())


def setup(bot) -> None:
    bot.add_cog(MiscCommands(bot))
