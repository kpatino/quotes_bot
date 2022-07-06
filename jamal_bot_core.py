#        __                          __       ____          __
#       / /____ _ ____ ___   ____ _ / /      / __ ) ____   / /_
#  __  / // __ `// __ `__ \ / __ `// /      / __  |/ __ \ / __/
# / /_/ // /_/ // / / / / // /_/ // /      / /_/ // /_/ // /_
# \____/ \__,_//_/ /_/ /_/ \__,_//_/______/_____/ \____/ \__/
#                                 /_____/

import asyncio
import logging
from datetime import datetime

import disnake
import pytz
from disnake.ext import commands
from environs import Env
from mcstatus import JavaServer

import jamal_bot_database

# Load environment variables
env = Env()
env.read_env()

discord_admin_role_id = env.int("DISCORD_ADMIN_ROLE_ID")
discord_api_key = env("DISCORD_API_KEY")
discord_mod_role_id = env.int("DISCORD_MOD_ROLE_ID")
discord_bot_activity = env.str("DISCORD_BOT_ACTIVITY", "Warframe")
discord_bot_prefixes = env.list("DISCORD_BOT_PREFIXES", 'jamal ,Jamal ,JAMAL ')
default_server_address = env("DEFAULT_SERVER_ADDRESS")
log_level = env.log_level("LOG_LEVEL", 'INFO')
timezone_list = env.list("TIMEZONE_LIST", 'Europe/London,US/Pacific')

# Logging configuration
log_format = '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
logfilename = (
    'jamal_bot_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.log')
logging.basicConfig(level=log_level, format=log_format, datefmt=date_format)
logger = logging.getLogger('disnake')
logger.setLevel(log_level)
handler = logging.FileHandler(filename=logfilename, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
logger.addHandler(handler)


# Use prefixes from environment variable or use fallback
# Will no longer be needed after switching to slash commands
def get_prefix(client, message):
    return commands.when_mentioned_or(*discord_bot_prefixes)(client, message)


intents = disnake.Intents.default()
intents.guild_messages = True
intents.message_content = True

# Requires jamal with a space in order to register
jamal_bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    case_insensitive=True)


@jamal_bot.event
async def on_ready():
    logging.info(f'Logged in as: {jamal_bot.user.name} - {jamal_bot.user.id}')
    logging.info(f'disnake version: {disnake.__version__}')
    activity = disnake.Game(name=discord_bot_activity)
    await jamal_bot.change_presence(
        status=disnake.Status.online,
        activity=activity)
    # Logging done lets Pterodactyl know that it's ready
    logging.info('Done')


# Ignore in DMs
@jamal_bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


# Error handling
# Does not work for subcommands
@jamal_bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required argument, try `jamal help` for help')
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send('Missing required role')


@jamal_bot.command(
    name='list',
    description='List available names from the database')
async def list_names(ctx):
    await ctx.send(jamal_bot_database.get_names())


@jamal_bot.slash_command(
    name='list',
    description='List available names from the database')
async def slash_list_names(inter):
    await inter.response.send_message(jamal_bot_database.get_names())


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
    if jamal_bot_database.check_name(name) is True:
        return jamal_bot_database.get_quote(name)
    else:
        return f'The name "{name}" is not in the database'


@jamal_bot.command(description='Access a random quote by name')
async def access(ctx, input_name: str):
    await ctx.send(access_command(input_name))


@jamal_bot.slash_command(
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
        inter: disnake.CommandInteraction, string: str):
    string = string.lower()
    return [name for name in jamal_bot_database.get_names_list()
            if string in name.lower()]


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
    if jamal_bot_database.check_name(name) is True:
        return f'The name "{name}" is already in the database'
    else:
        try:
            jamal_bot_database.add_name(name)
            return f'{author} added "{name}" to the database'
        except Exception:
            return 'Could not add the name to the database'


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
    try:
        if jamal_bot_database.check_name(name) is False:
            return f'The name "{name}" is not in the database'
        else:
            if quote == "":
                return 'A quote was not provided, try `jamal help` for help'
            else:
                jamal_bot_database.add_quote(name, quote)
                return f'Added “{quote}” to {name}'
    except Exception:
        return 'Could not add the quote to the database'


@jamal_bot.group(name='add', description='Add a name or quote to the database')
async def add(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Missing required argument, '
                       'try `jamal help add` for help')


@add.command(
    name='name',
    description='Add a "name" to the database')
@commands.has_any_role(
    discord_admin_role_id,
    discord_mod_role_id)
async def add_name(ctx, input_name: str):
    await ctx.send(add_name_command(ctx.message.author.mention, input_name))


@add.command(
    name='quote',
    description='Add a quote to the database.')
async def add_quote(ctx, input_name: str, *, arg):
    await ctx.send(add_quote_command(input_name, arg))


@jamal_bot.slash_command(
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
        inter: disnake.CommandInteraction, string: str):
    string = string.lower()
    return [name for name in jamal_bot_database.get_names_list()
            if string in name.lower()]


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
    try:
        if jamal_bot_database.check_name(name) is False:
            return f'"{name}" is not in the database'
        else:
            jamal_bot_database.remove_name(name)
            return f'{author} removed "{name}" from the database'
    except Exception:
        return 'Could not remove name from the database'


@jamal_bot.group(
    description='Remove a name and their quotes from the database')
async def remove(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Missing required argument, '
                       'try `jamal help remove` for help')


@remove.command(
    name='name',
    description='Remove a name and their quotes from the database')
@commands.has_any_role(
    discord_admin_role_id,
    discord_mod_role_id)
async def rm_name(ctx, input_name: str):
    ctx.send(remove_name_command(ctx.message.author.mention, input_name))


@jamal_bot.slash_command(
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
        inter: disnake.CommandInteraction, string: str):
    string = string.lower()
    return [name for name in jamal_bot_database.get_names_list()
            if string in name.lower()]


@jamal_bot.command(description='Get a random quote and guess who said it')
async def quotes(ctx):
    name = jamal_bot_database.random_name()
    await ctx.send(f'Who said “{jamal_bot_database.get_quote(name)}”')

    try:
        guess = await jamal_bot.wait_for('message', timeout=6.0)
    except asyncio.TimeoutError:
        return await ctx.channel.send(f'TOOK TO LONG it was {name}')

    if (str(guess.content)).lower() == name:
        await ctx.channel.send(f'You got em <@{guess.author.id}>')
    else:
        await ctx.channel.send(f'<@{guess.author.id}> YOU\'RE WRONG‼'
                               f'IT WAS {name.upper()}‼')


@jamal_bot.slash_command(
    name='quotes',
    description='Get a random quote and guess who said it')
async def slash_quotes(inter):
    name = jamal_bot_database.random_name()
    guess = ''
    await inter.response.send_message(
        f'Who said “{jamal_bot_database.get_quote(name)}”')

    try:
        guess = await jamal_bot.wait_for('message', timeout=6.0)
    except asyncio.TimeoutError:
        await inter.channel.send(f'TOOK TO LONG it was {name}')

    if (str(guess.content)).lower() == name:
        await inter.channel.send(f'You got em <@{guess.author.id}>')
    else:
        await inter.channel.send(f'<@{guess.author.id}> YOU\'RE WRONG‼ '
                                 f'IT WAS {name.upper()}‼')


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


# {server_address} is optional
@jamal_bot.command(description='Get the status of a Minecraft server.')
async def status(ctx, server_address=default_server_address):
    logging.info(f"{ctx.message.author} used status command")
    await ctx.send(embed=await status_embed(server_address))


@jamal_bot.slash_command(
    name='status',
    description='Get the status of a Minecraft server. '
                f'By default query {default_server_address}',
    options=[
        disnake.Option(
            "server_address",
            description='Server address or IP to query')])
async def slash_status(
    inter: disnake.ApplicationCommandInteraction,
        server_address=default_server_address):
    logging.info(f"{inter.user} used status slash command")
    await inter.response.defer(with_message=True)
    await inter.followup.send(embed=await status_embed(server_address))


def current_time(zone: str):
    """
    Return the current time at the provided zone

    Args:
        zone (str): Timezone
    Returns
        str: Current formatted time in a string
    """
    return datetime.now(pytz.timezone(zone)).strftime('%b %d %I:%M %p (%H:%M)')


def timezone_embed():
    """
    Create an embed with the current time in different timezones and return it.

    Returns
        embed: Time in different timezones
    """

    embed = disnake.Embed(colour=disnake.Colour.purple())
    embed.set_author(name='jamal bot time')

    for tz in timezone_list:
        embed.add_field(
            name=tz,
            value=current_time(tz),
            inline=False)

    return embed


@jamal_bot.command(description='Get the current time in different timezones')
async def time(ctx):
    await ctx.send(embed=timezone_embed())


@jamal_bot.slash_command(
    name='time',
    description='Get the current time in different timezones')
async def slash_time(inter):
    await inter.response.send_message(embed=timezone_embed())

if __name__ == '__main__':
    # Only creates the database if it doesn't exist
    jamal_bot_database.create_db('jamal_bot_quotes.db')

    jamal_bot.run(discord_api_key)
