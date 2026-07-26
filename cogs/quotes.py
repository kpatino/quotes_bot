# SPDX-FileCopyrightText: 2026 Kevin Patino
# SPDX-License-Identifier: MIT

import asyncio
import logging

import disnake
from disnake.ext import commands, tasks

import database
from config import Config

module_logger = logging.getLogger(f"__main__.{__name__}")


def access_command(guild_id: int, name: str) -> str:
    """Return a random quote from the database by name.

    Args:
        guild_id (int): Discord server ID to scope the query to.
        name (str): Name in the database with quotes.

    Returns:
        str: A random quote or an error message if not found.
    """
    name = name.lower()
    if database.verify_name(guild_id, name) is True:
        return database.get_random_quote(guild_id, name)
    else:
        return f'The name "{name}" is not in the database'


def add_name_command(guild_id: int, added_by: int, author, name: str) -> str:
    """Add a name to the database.

    Args:
        guild_id (int): Discord server ID to scope the entry to.
        added_by (int): Discord user ID who added the name.
        author: Pass either ctx.message.author.mention or inter.author.mention.
        name (str): Name to add to the database.

    Returns:
        str: Status message indicating success or that the name already exists.
    """
    name = name.lower()
    if database.verify_name(guild_id, name) is True:
        return f'The name "{name}" is already in the database'
    else:
        database.add_name(guild_id, name, added_by)
        return f'{author} added "{name}" to the database'


def add_quote_command(guild_id: int, added_by: int, name: str, quote: str) -> str:
    """Add a quote attributed to a name in the database.

    Args:
        guild_id (int): Discord server ID to scope the entry to.
        added_by (int): Discord user ID who added the quote.
        name (str): Name for quote attribution.
        quote (str): The quote text.

    Returns:
        str: Status message indicating success or failure.
    """
    name = name.lower()
    if database.verify_name(guild_id, name) is False:
        return f'The name "{name}" is not in the database'
    else:
        if quote == "":
            return "A quote was not provided"
        else:
            database.add_quote(guild_id, name, quote, added_by)
            return f"Added \u201c{quote}\u201d to {name}"


def remove_name_command(guild_id: int, author, name: str) -> str:
    """Remove a name and all associated quotes from the database. Not reversible.

    Args:
        guild_id (int): Discord server ID to scope the query to.
        author: Pass either ctx.message.author.mention or inter.author.mention.
        name (str): Name to remove from the database.

    Returns:
        str: Status message indicating success or that the name was not found.
    """
    name = name.lower()
    if database.verify_name(guild_id, name) is False:
        return f'"{name}" is not in the database'
    else:
        database.remove_name(guild_id, name)
        return f'{author} removed "{name}" from the database'


class QuotesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.names_by_guild: dict[int, list[str]] = {}
        self.retrieve_names_loop.start()

    @commands.contexts(bot_dm=False)
    @tasks.loop(seconds=15.0)
    async def retrieve_names_loop(self) -> None:
        for guild in self.bot.guilds:
            self.names_by_guild[guild.id] = database.get_names_list(guild.id)

    @commands.command(name="list", description="List available names from the database")
    @commands.guild_only()
    async def list_names(self, ctx) -> None:
        module_logger.info(f'Message command "list" executed by {ctx.author.id}')
        await ctx.reply(database.get_names(ctx.guild.id), mention_author=False)

    @commands.slash_command(
        name="list", description="List available names from the database"
    )
    @commands.guild_only()
    async def slash_list_names(self, inter: disnake.CommandInteraction) -> None:
        module_logger.info(f'Slash command "list" executed by {inter.author.id}')
        await inter.response.send_message(database.get_names(inter.guild_id))

    @commands.command(description="Access a random quote by name")
    @commands.guild_only()
    async def access(self, ctx, input_name: str) -> None:
        module_logger.info(f'Message command "access" executed by {ctx.author.id}')
        await ctx.reply(access_command(ctx.guild.id, input_name), mention_author=False)

    @commands.slash_command(
        name="access",
        description="Access a random quote by name",
        options=[
            disnake.Option(
                "name",
                description="Get a random quote attributed to this name",
                required=True,
            )
        ],
    )
    @commands.guild_only()
    async def slash_access(self, inter: disnake.CommandInteraction, name: str) -> None:
        module_logger.info(f'Slash command "access" executed by {inter.author.id}')
        await inter.response.send_message(access_command(inter.guild_id, name))

    @slash_access.autocomplete("name")
    async def slash_access_autocomp(
        self, inter: disnake.CommandInteraction, user_input: str
    ):
        user_input = user_input.lower()
        names = self.names_by_guild.get(inter.guild_id, [])
        return [name for name in names if user_input in name.lower()]

    @commands.group(name="add", description="Add a name or quote to the database")
    @commands.guild_only()
    async def add(self, ctx) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.reply("Missing required argument", mention_author=False)

    @add.command(name="name", description='Add a "name" to the database')
    @commands.has_any_role(Config.discord_admin_role_id, Config.discord_mod_role_id)
    async def add_name(self, ctx, input_name: str) -> None:
        module_logger.info(
            f'Message command "add name" with input: [{input_name}] executed by {ctx.author.id}'
        )
        await ctx.reply(
            add_name_command(ctx.guild.id, ctx.author.id, ctx.message.author.mention, input_name),
            mention_author=False,
        )

    @add.command(name="quote", description="Add a quote to the database.")
    async def add_quote(self, ctx, input_name: str, *, arg):
        module_logger.info(
            f'Message command "add quote" with inputs: [{input_name}] [{arg}] executed by {ctx.author.id}'
        )
        await ctx.reply(add_quote_command(ctx.guild.id, ctx.author.id, input_name, arg), mention_author=False)

    @commands.slash_command(
        name="add", description="Add a name or quote to the database"
    )
    @commands.guild_only()
    async def slash_add(self, inter: disnake.CommandInteraction) -> None:
        pass

    @slash_add.sub_command(
        name="name",
        description='Add a "name" to the database',
        options=[
            disnake.Option(
                "name", description="Name to add to the database", required=True
            )
        ],
    )
    async def slash_add_name(
        self, inter: disnake.CommandInteraction, name: str
    ) -> None:
        module_logger.info(
            f'Message command "add name" with input: [{name}] executed by {inter.author.id}'
        )
        await inter.response.send_message(add_name_command(inter.guild_id, inter.author.id, inter.author.mention, name))

    @slash_add.sub_command(
        name="quote",
        description="Add a quote to the database.",
        options=[
            disnake.Option(
                "name", description="Name to attribute the quote", required=True
            ),
            disnake.Option(
                "quote",
                description="The quote to record to the database",
                required=True,
            ),
        ],
    )
    async def slash_add_quote(
        self, inter: disnake.CommandInteraction, name: str, quote: str
    ) -> None:
        module_logger.info(
            f'Slash command "add quote" with inputs: [{name}] [{quote}] executed by {inter.author.id}'
        )
        await inter.response.send_message(add_quote_command(inter.guild_id, inter.author.id, name, quote))

    @slash_add_quote.autocomplete("name")
    async def slash_add_quote_autocomp(
        self, inter: disnake.CommandInteraction, string: str
    ):
        string = string.lower()
        names = self.names_by_guild.get(inter.guild_id, [])
        return [name for name in names if string in name.lower()]

    @commands.group(description="Remove a name and their quotes from the database")
    @commands.guild_only()
    async def remove(self, ctx) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.reply("Missing required argument", mention_author=False)

    @remove.command(
        name="name", description="Remove a name and their quotes from the database"
    )
    @commands.has_any_role(Config.discord_admin_role_id, Config.discord_mod_role_id)
    async def rm_name(self, ctx, input_name: str) -> None:
        module_logger.info(
            f'Message command "remove name" with inputs: [{input_name}] executed by {ctx.author.id}'
        )
        await ctx.reply(
            remove_name_command(ctx.guild.id, ctx.message.author.mention, input_name),
            mention_author=False,
        )

    @commands.slash_command(
        name="remove", description="Remove a name or quote to the database"
    )
    @commands.guild_only()
    async def slash_remove(self, inter: disnake.CommandInteraction) -> None:
        pass

    @slash_remove.sub_command(
        name="name", description="Remove a name and their quotes from the database"
    )
    async def slash_remove_name(self, inter, name: str) -> None:
        module_logger.info(
            f'Slash command "remove name" with inputs: [{name}] executed by {inter.author.id}'
        )
        await inter.response.send_message(
            remove_name_command(inter.guild_id, inter.author.mention, name)
        )

    @slash_remove_name.autocomplete("name")
    async def slash_remove_name_autocomp(
        self, inter: disnake.CommandInteraction, string: str
    ):
        string = string.lower()
        names = self.names_by_guild.get(inter.guild_id, [])
        return [name for name in names if string in name.lower()]

    @commands.command(description="Get a random quote and guess who said it")
    @commands.guild_only()
    async def quotes(self, ctx) -> None:
        module_logger.info(f'Message command "quotes" executed by {ctx.author.id}')
        name = database.get_random_name(ctx.guild.id)
        await ctx.reply(
            f"Who said \u201c{database.get_random_quote(ctx.guild.id, name)}\u201d", mention_author=False
        )

        try:
            guess = await ctx.bot.wait_for("message", timeout=6.0)

            if guess.content.lower() == name:
                await ctx.channel.send(f"You got em <@{guess.author.id}>")
            else:
                await ctx.channel.send(
                    f"<@{guess.author.id}> YOU'RE WRONG\u203cIT WAS {name.upper()}\u203c"
                )
        except TimeoutError:
            return await ctx.channel.send(f"TOOK TO LONG it was {name}")

    @commands.slash_command(
        name="quotes", description="Get a random quote and guess who said it"
    )
    @commands.guild_only()
    async def slash_quotes(self, inter: disnake.CommandInteraction) -> None:
        module_logger.info(f'Slash command "quotes" executed by {inter.author.id}')
        name = database.get_random_name(inter.guild_id)
        await inter.response.send_message(
            f"Who said \u201c{database.get_random_quote(inter.guild_id, name)}\u201d"
        )

        try:
            guess = await inter.bot.wait_for("message", timeout=6.0)

            if guess.content.lower() == name:
                await inter.channel.send(f"You got em <@{guess.author.id}>")
            else:
                await inter.channel.send(
                    f"<@{guess.author.id}> YOU'RE WRONG\u203c IT WAS {name.upper()}\u203c"
                )
        except TimeoutError:
            await inter.channel.send(f"YOU TOOK TO LONG it was {name}")


def setup(bot) -> None:
    bot.add_cog(QuotesCommands(bot))
