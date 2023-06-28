# SPDX-FileCopyrightText: 2023 Kevin Patino
# SPDX-License-Identifier: MIT

import asyncio
import logging

import disnake
from disnake.ext import commands
from mcstatus import JavaServer

from config import Config

module_logger = logging.getLogger(f'__main__.{__name__}')


async def status_embed(server_address: str) -> disnake.Embed:
    """
    Returns a disnake embed containing the status of a Minecraft server at the
    provided address

    Args:
        server_address (str): Server address or IP
    Returns:
        embed: Server status information
    """

    try:
        module_logger.info(f'Looking up Minecraft server "{server_address}"')
        server = JavaServer.lookup(server_address)
        server_status = await server.async_status()
        module_logger.debug(f'Succesful lookup of "{server_address}"')
        module_logger.debug(f'{server_status.raw}')
        module_logger.debug(f'Pinging "{server_address}"')
        server_latency = round(server_status.latency, 2)
        module_logger.debug(f'Got a latency of {server_latency}ms')
        server_status_embed = disnake.Embed(
            title=server_address,
            description=server_status.version.name,
            colour=disnake.Colour.green())
        server_status_embed.add_field(
            name='Description',
            value=f'```\u200b{server_status.description}```',  # Unicode blank prevents an empty "value"
            inline=False)
        server_status_embed.add_field(
            name='Count',
            value=f'{server_status.players.online}/{server_status.players.max}',
            inline=True)

        try:
            module_logger.info(f'Querying server at {server_address}')
            query = await server.async_query()
            module_logger.info(f'Successfully queried server at {server_address}')
            server_players = (', '.join(query.players.names))
            server_status_embed.add_field(
                name='Players',
                value=f'\u200b{server_players}',  # Unicode blank prevents an empty "value"
                inline=True)
            server_status_embed.set_footer(text=f'Ping: {server_latency} ms')
            return server_status_embed

        except asyncio.exceptions.TimeoutError:
            module_logger.warn(f'Failed to query server at {server_address}')
            module_logger.warn(f'Fallback to lookup instead for {server_address}')
            server_status_embed.set_footer(text=f'Ping: {server_latency} ms')
            return server_status_embed

    except asyncio.exceptions.TimeoutError:
        module_logger.warn(f'Could not lookup server at {server_address}')
        error_embed = disnake.Embed(title='Could not contact server', colour=disnake.Colour.red())
        return error_embed


class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(description='Get the status of a Minecraft server.')
    async def status(self, ctx, server_address=Config.default_server_address) -> None:
        module_logger.info(f'Message command "status" executed by {ctx.author.id}')
        await ctx.trigger_typing()
        await ctx.reply(embed=await status_embed(server_address), mention_author=False)

    @commands.slash_command(name='status',
                            description='Get the status of a Minecraft server. '
                            f'By default query {Config.default_server_address}',
                            options=[disnake.Option(
                                        'server_address',
                                        description='Server address or IP to query')])
    async def slash_status(self, inter: disnake.ApplicationCommandInteraction,
                           server_address=Config.default_server_address) -> None:
        module_logger.info(f'Slash command "status" executed by {inter.author.id}')
        await inter.response.defer(with_message=True)
        await inter.followup.send(embed=await status_embed(server_address))


def setup(bot) -> None:
    bot.add_cog(StatusCommands(bot))
