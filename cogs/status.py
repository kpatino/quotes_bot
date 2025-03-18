# SPDX-FileCopyrightText: 2024 Kevin Patino
# SPDX-FileCopyrightText: 2023 py-mine
# SPDX-License-Identifier: Apache-2.0 AND MIT

import asyncio
import logging

import disnake
from disnake.ext import commands
from mcstatus import JavaServer
from mcstatus.status_response import JavaStatusResponse
from mcstatus.querier import QueryResponse

from config import Config

module_logger = logging.getLogger(f'__main__.{__name__}')


async def status(host: str) -> JavaStatusResponse | QueryResponse:
    """
    Get status from server, which can be a normal status or GameSpy4 query

    The function will ping server for status and query in one time, and will try to prefer the query.
    """
    success_task = await handle_exceptions(*(
            await asyncio.wait({
                    asyncio.create_task(handle_java_query(host), name="Get query as Java"),
                    asyncio.create_task(handle_java_status(host), name="Get status as Java"),
                },
                return_when=asyncio.FIRST_COMPLETED,
                timeout=10
            )
        )
    )

    if success_task is None:
        raise ValueError("No tasks were successful. Is server offline?")

    return success_task.result()


async def latency(host: str) -> float:
    """
    Get latency from server
    """
    success_task = await handle_exceptions(*(
            await asyncio.wait({
                    asyncio.create_task(handle_latency(host), name="Get server latency"),
                },
                return_when=asyncio.FIRST_COMPLETED,
            )
        )
    )

    if success_task is None:
        raise ValueError("No tasks were successful. Is server offline?")

    return success_task.result()


async def handle_exceptions(done: set[asyncio.Task], pending: set[asyncio.Task]) -> asyncio.Task | None:
    """
    Handle exceptions from tasks.

    Also, cancel all pending tasks, if found correct one.
    """
    if len(done) == 0:
        raise ValueError("No tasks was given to `done` set.")

    for i, task in enumerate(done):
        if task.exception() is not None:
            if len(pending) == 0:
                continue

            if i == len(done) - 1:  # firstly check all items from `done` set, and then handle pending set
                return await handle_exceptions(*(await asyncio.wait(pending, return_when=asyncio.FIRST_EXCEPTION)))
        else:
            for pending_task in pending:
                pending_task.cancel()
            return task


async def handle_java_status(host: str) -> JavaStatusResponse | None:
    """A wrapper around mcstatus, to compress it in one function."""
    try:
        async with asyncio.timeout(6):
            status = await (await JavaServer.async_lookup(host)).async_status()
            await asyncio.sleep(1)
            return await status
    except TimeoutError:
        module_logger.warn("Timed out, something went wrong. Is the server down?")
        raise
    except ValueError:
        module_logger.warn("Did not succeed, is the server down?")
        raise
    except Exception as e:
        module_logger.warn(e)
        raise


async def handle_java_query(host: str) -> QueryResponse | None:
    """A wrapper around mcstatus, to compress it in one function."""
    try:
        async with asyncio.timeout(4):
            return await (await JavaServer.async_lookup(host)).async_query()
    except TimeoutError:
        module_logger.warn("Query timed out, does the server have enable-query=false?")
        raise
    except ValueError:
        module_logger.warn("Query did not succeed, does the server provided exist?")
        raise
    except Exception as e:
        module_logger.warn(e)
        raise


async def handle_latency(host: str) -> float:
    """A wrapper around mcstatus, to compress it in one function."""
    return await (await JavaServer.async_lookup(host)).async_ping()


async def status_embed(server_address: str) -> disnake.Embed:
    """
    Returns a disnake embed containing the status of a Minecraft server at the
    provided address

    Args:
        server_address (str): Server address or IP
    Returns:
        embed: Server status information
    """

    error_embed = disnake.Embed(title=server_address,
                                description="Could not contact server",
                                colour=disnake.Colour.red())
    try:
        server_status = await status(server_address)

        if isinstance(server_status, QueryResponse):
            module_logger.debug("Sending QueryResponse")
            server_latency = await latency(server_address)  # Query doesn't provide latency
            server_status_embed = disnake.Embed(
                title=server_address,
                description=f'{server_status.software.brand} {server_status.software.version}',
                colour=disnake.Colour.green())
            server_status_embed.add_field(
                name='Description',
                value=f'```ansi\n\u200b{server_status.motd.to_ansi()}```',
                inline=False)
            server_status_embed.add_field(
                name='Count',
                value=f'{server_status.players.online}/{server_status.players.max}',
                inline=True)
            server_players = (', '.join(server_status.players.names))
            server_status_embed.add_field(
                name='Players',
                value=f'\u200b{server_players}',  # Unicode blank prevents an empty "value"
                inline=True)
            server_status_embed.set_footer(text=f'Ping: {int(server_latency)} ms')
            return server_status_embed

        elif isinstance(server_status, JavaStatusResponse):
            module_logger.warn("Sending JavaStatusResponse, did QueryResponse fail?")
            server_status_embed = disnake.Embed(
                title=server_address,
                description=server_status.version.name,
                colour=disnake.Colour.green())
            server_status_embed.add_field(
                name='Description',
                value=f'```ansi\n\u200b{server_status.motd.to_ansi()}```',  # Unicode blank prevents an empty "value"
                inline=False)
            server_status_embed.add_field(
                name='Count',
                value=f'{server_status.players.online}/{server_status.players.max}',
                inline=True)
            server_status_embed.set_footer(text=f'Ping: {int(server_status.latency)} ms')
            return server_status_embed

        else:
            raise TypeError

    except (asyncio.exceptions.TimeoutError, TypeError, ValueError) as e:
        module_logger.warn(e)
        module_logger.warning(f'Could not lookup server at {server_address}')
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
