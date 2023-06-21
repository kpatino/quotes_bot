# SPDX-FileCopyrightText: 2023 Kevin Patino
# SPDX-License-Identifier: MIT

import asyncio
import logging

import disnake
from disnake.ext import commands
from mcstatus import JavaServer

from config import Config


async def status_embed(server_address: str):
    """
    Returns a disnake embed containing the status of a Minecraft server at the
    provided address

    Args:
        server_address (str): Server address or IP
    Returns:
        embed: Server status information
    """

    try:
        logging.info(f"Looking up {server_address}")
        server = JavaServer.lookup(server_address)
        server_status = await server.async_status()
        server_latency = round(server_status.latency, 2)
        server_status_embed = disnake.Embed(
            title=server_address,
            description=server_status.version.name,
            colour=disnake.Colour.green())
        server_status_embed.add_field(
            name='Description',
            # Unicode blank prevents an empty "value"
            value=f'```\u200b{server_status.description}```',
            inline=False)
        server_status_embed.add_field(
            name='Count',
            value=f'{server_status.players.online}/{server_status.players.max}',
            inline=True)

        try:
            logging.info(f"Querying server at {server_address}")
            query = await server.async_query()
            logging.info(f"Successfully queried server at {server_address}")
            server_players = (", ".join(query.players.names))
            server_status_embed.add_field(
                name="Players",
                # Unicode blank prevents an empty "value"
                value=f'\u200b{server_players}',
                inline=True)
            server_status_embed.set_footer(
                text=f'Ping: {server_latency} ms')
            return server_status_embed

        except asyncio.exceptions.TimeoutError:
            logging.info(f"Failed to query server at {server_address}")
            logging.info(f"Using lookup instead for {server_address}")
            server_status_embed.set_footer(text=f'Ping: {server_latency} ms')
            return server_status_embed

    except asyncio.exceptions.TimeoutError:
        logging.info(f"Could not lookup server at {server_address}")
        error_embed = disnake.Embed(
            title='Could not contact server',
            colour=disnake.Colour.red())
        return error_embed


class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(description='Get the status of a Minecraft server.')
    async def status(self, ctx, server_address=Config.default_server_address) -> None:
        await ctx.trigger_typing()
        await ctx.reply(embed=await status_embed(server_address), mention_author=False)

    @commands.slash_command(name='status',
                            description='Get the status of a Minecraft server. '
                            f'By default query {Config.default_server_address}',
                            options=[disnake.Option(
                                        "server_address",
                                        description='Server address or IP to query')])
    async def slash_status(self, inter: disnake.ApplicationCommandInteraction,
                           server_address=Config.default_server_address) -> None:
        await inter.response.defer(with_message=True)
        await inter.followup.send(embed=await status_embed(server_address))


def setup(bot) -> None:
    bot.add_cog(StatusCommands(bot))
