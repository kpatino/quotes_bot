# SPDX-FileCopyrightText: 2023 Kevin Patino
# SPDX-License-Identifier: MIT

import asyncio

import disnake
from disnake.ext import commands, tasks

import database
from config import Config


def access_command(name: str):
    """
    Returns a random quote from the database by name.
    If there are no quotes return a string saying so.

    Args:
        name (str): Name in the database with quotes

    Returns:
        str: Message with status information
    """
    name = name.lower()
    if database.verify_name(name) is True:
        return database.get_random_quote(name)
    else:
        return f'The name "{name}" is not in the database'


def add_name_command(author, name: str):
    """
    Name to add to the database.

    Args:
        author : Pass either ctx.message.author.mention or inter.author.mention
        name (str): User provided name to add to the database

    Returns:
        str: Message with status information
    """
    name = name.lower()
    if database.verify_name(name) is True:
        return f'The name "{name}" is already in the database'
    else:
        database.add_name(name)
        return f'{author} added "{name}" to the database'


def add_quote_command(name: str, quote: str):
    """
    Add a quote to the database attributed to a name
    Return message with information on whether it was successful.

    Args:
        name (str): Name for quote attribution
        quote (str): The quote in a string value

    Returns:
        str: Message with status information
    """
    name = name.lower()
    if database.verify_name(name) is False:
        return f'The name "{name}" is not in the database'
    else:
        if quote == "":
            return 'A quote was not provided'
        else:
            database.add_quote(name, quote)
            return f'Added “{quote}” to {name}'


def remove_name_command(author, name: str):
    """
    Removes name and the associated quotes from the database. Cannot be undone.

    Args:
        author : Pass either ctx.message.author.mention or inter.author.mention
        name (str): Name to remove from the database
    Returns:
        str: Message with status
    """
    name = name.lower()
    if database.verify_name(name) is False:
        return f'"{name}" is not in the database'
    else:
        database.remove_name(name)
        return f'{author} removed "{name}" from the database'


class QuotesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.names_list = ''
        self.retrieve_names_loop.start()

    @tasks.loop(seconds=15.0)
    async def retrieve_names_loop(self):
        self.names_list = database.get_names_list()

    @commands.command(
        name='list',
        description='List available names from the database')
    async def list_names(self, inter):
        await self.send(database.get_names())

    @commands.slash_command(
        name='list',
        description='List available names from the database')
    async def slash_list_names(inter):
        await inter.response.send_message(database.get_names())

    @commands.command(description='Access a random quote by name')
    async def access(self, inter, input_name: str):
        await inter.send(access_command(input_name))

    @commands.slash_command(
        name='access',
        description='Access a random quote by name',
        options=[
            disnake.Option(
                "name",
                description="Get a random quote attributed to this name",
                required=True)]
        )
    async def slash_access(inter: disnake.CommandInteraction, name: str):
        await inter.response.send_message(access_command(name))

    @slash_access.autocomplete('name')
    async def slash_access_autocomp(
            self, inter: disnake.CommandInteraction, user_input: str):
        user_input = user_input.lower()
        return [name for name in self.names_list if user_input in name.lower()]

    @commands.group(name='add', description='Add a name or quote to the database')
    async def add(self, inter):
        if self.invoked_subcommand is None:
            await self.send('Missing required argument')

    @add.command(
        name='name',
        description='Add a "name" to the database')
    @commands.has_any_role(
        Config.discord_admin_role_id,
        Config.discord_mod_role_id)
    async def add_name(ctx, input_name: str):
        await ctx.send(commands.add_name_command(ctx.message.author.mention, input_name))

    @add.command(
        name='quote',
        description='Add a quote to the database.')
    async def add_quote(ctx, input_name: str, *, arg):
        await ctx.send(add_quote_command(input_name, arg))

    @commands.slash_command(
        name='add',
        description='Add a name or quote to the database',
        dm_permission=False)
    async def slash_add(inter):
        pass

    @slash_add.sub_command(
        name='name',
        description='Add a "name" to the database',
        options=[
            disnake.Option(
                "name",
                description="Name to add to the database",
                required=True)])
    async def slash_add_name(inter, name: str):
        await inter.response.send_message(
            add_name_command(inter.author.mention, name))

    @slash_add.sub_command(
        name='quote',
        description='Add a quote to the database.',
        options=[
            disnake.Option(
                "name",
                description="Name to attribute the quote",
                required=True),
            disnake.Option(
                "quote",
                description="The quote to record to the database",
                required=True)])
    async def slash_add_quote(
        inter: disnake.CommandInteraction,
            name: str, quote: str):
        await inter.response.send_message(add_quote_command(name, quote))

    @slash_add_quote.autocomplete('name')
    async def slash_add_quote_autocomp(
            self, inter: disnake.CommandInteraction, string: str):
        string = string.lower()
        return [name for name in self.names_list if string in name.lower()]

    @commands.group(
        description='Remove a name and their quotes from the database')
    async def remove(ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Missing required argument')

    @remove.command(
        name='name',
        description='Remove a name and their quotes from the database')
    @commands.has_any_role(
        Config.discord_admin_role_id,
        Config.discord_mod_role_id)
    async def rm_name(ctx, input_name: str):
        ctx.send(remove_name_command(ctx.message.author.mention, input_name))

    @commands.slash_command(
        name='remove',
        description='Remove a name or quote to the database',
        dm_permission=False)
    async def slash_remove(inter):
        pass

    @slash_remove.sub_command(
        name='name',
        description='Remove a name and their quotes from the database')
    async def slash_remove_name(inter, name: str):
        await inter.response.send_message(
            remove_name_command(inter.author.mention, name))

    @slash_remove_name.autocomplete('name')
    async def slash_remove_name_autocomp(
            self, inter: disnake.CommandInteraction, string: str):
        string = string.lower()
        return [name for name in self.names_list if string in name.lower()]

    @commands.command(description='Get a random quote and guess who said it')
    async def quotes(self, inter):
        name = database.get_random_name()
        await self.send(f'Who said “{database.get_random_quote(name)}”')

        try:
            guess = await self.bot.wait_for('message', timeout=6.0)

            if guess.content.lower() == name:
                await self.channel.send(f'You got em <@{guess.author.id}>')
            else:
                await self.channel.send(f'<@{guess.author.id}> YOU\'RE WRONG‼'
                                        f'IT WAS {name.upper()}‼')
        except asyncio.TimeoutError:
            return await self.channel.send(f'TOOK TO LONG it was {name}')

    @commands.slash_command(
        name='quotes',
        description='Get a random quote and guess who said it')
    async def slash_quotes(self, inter):
        name = database.get_random_name()
        await inter.response.send_message(
            f'Who said “{database.get_random_quote(name)}”')

        try:
            guess = await self.bot.wait_for('message', timeout=6.0)

            if guess.content.lower() == name:
                await inter.channel.send(f'You got em <@{guess.author.id}>')
            else:
                await inter.channel.send(f'<@{guess.author.id}> YOU\'RE WRONG‼ '
                                         f'IT WAS {name.upper()}‼')
        except asyncio.TimeoutError:
            await inter.channel.send(f'YOU TOOK TO LONG it was {name}')


def setup(bot):
    bot.add_cog(QuotesCommands(bot))
