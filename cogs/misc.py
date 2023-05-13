# SPDX-FileCopyrightText: 2023 Kevin Patino
# SPDX-License-Identifier: MIT

from datetime import datetime

import asyncio
import disnake
import pytz
import logging
from disnake.ext import commands

from config import Config


class MiscFunctions():
    async def timezone_embed():
        """
        Create an embed with the current time in different timezones and return it.

        Returns
            embed: Time in different timezones
        """

        embed = disnake.Embed(colour=disnake.Colour.purple())
        embed.set_author(name='Time')

        for tz in Config.timezone_list:
            embed.add_field(
                name=tz,
                value=datetime.now(
                    pytz.timezone(tz)).strftime('%b %d %I:%M %p (%H:%M)'),
                inline=False)

        return embed


class MiscCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(description='Get the current time in different timezones')
    async def time(self, inter):
        await self.send(embed=await MiscFunctions.timezone_embed())

    @commands.slash_command(
        name='time',
        description='Get the current time in different timezones')
    async def slash_time(self, inter):
        await inter.response.send_message(embed=await MiscFunctions.timezone_embed())


def setup(bot):
    bot.add_cog(MiscCommands(bot))
