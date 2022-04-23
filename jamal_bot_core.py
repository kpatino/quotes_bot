#        __                          __       ____          __
#       / /____ _ ____ ___   ____ _ / /      / __ ) ____   / /_
#  __  / // __ `// __ `__ \ / __ `// /      / __  |/ __ \ / __/
# / /_/ // /_/ // / / / / // /_/ // /      / /_/ // /_/ // /_
# \____/ \__,_//_/ /_/ /_/ \__,_//_/______/_____/ \____/ \__/
#                                 /_____/

import asyncio
import logging
import os
from datetime import datetime

import disnake
import pytz
from disnake.ext import commands
from dotenv import load_dotenv
from mcstatus import JavaServer

import jamal_bot_database

# load environment variables from .env
load_dotenv()

# logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logfilename = 'jamal_bot_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.log'
logger = logging.getLogger('disnake')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=logfilename, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# only creates the database if it doesn't exist
jamal_bot_database.create_db('jamal_bot_quotes.db')


# in summary allow users to @mention the bot and use three different cased
# variations of "jamal " with a space
# will no longer be needed after switching to slash commands
def get_prefix(client, message):
    prefixes = ['jamal ', 'Jamal ', 'JAMAL ']
    return commands.when_mentioned_or(*prefixes)(client, message)


intents = disnake.Intents.default()
intents.guild_messages = True

# requires jamal with a space in order to register
jamal_bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    case_insensitive=True)


@jamal_bot.event
async def on_ready():
    print(f'\nLogged in as: {jamal_bot.user.name} - {jamal_bot.user.id}')
    print('disnake Version:', disnake.__version__)
    activity = disnake.Game(name='Warframe')
    await jamal_bot.change_presence(
        status=disnake.Status.online,
        activity=activity)
    # Printing done let's pterodactyl know that it's ready
    print('Done')


# ignore in DMs
@jamal_bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


# jamal error handling
# does not work for subcommands
@jamal_bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required argument, try `jamal help` for help')
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send('Missing required role')


@jamal_bot.command(description='List names available from the database')
async def list(ctx):
    await ctx.send(jamal_bot_database.get_names())


@jamal_bot.command(description='Access a random quote from somebody')
async def access(ctx, input_name: str):
    if jamal_bot_database.check_name(input_name.lower()) is True:
        await ctx.send(jamal_bot_database.get_quote(input_name.lower()))
    else:
        await ctx.send(f'"{input_name.lower()}" is not in the database')


@jamal_bot.group(name='add', description='Add a name or quote to the database')
async def add(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Missing required argument, try `jamal help add` for help')


@add.command(
    name='name',
    description='Add a "name" to the database')
@commands.has_any_role(
    int(os.getenv('ADMIN_ROLE_ID')),
    int(os.getenv('MOD_ROLE_ID')))
async def add_name(ctx, input_name: str):
    if jamal_bot_database.check_name(input_name) is True:
        await ctx.send(f'"{input_name.lower()}" is already in the database')
    else:
        jamal_bot_database.add_name(input_name.lower())
        await ctx.send(f'{ctx.message.author.mention} has added "{input_name.lower()}" to the database')


@add.command(
    name='quote',
    description='Add a quote to the database.')
@commands.has_any_role(
    int(os.getenv('ADMIN_ROLE_ID')),
    int(os.getenv('MOD_ROLE_ID')))
async def add_quote(ctx, input_name: str, *, arg):
    if jamal_bot_database.check_name(input_name.lower()) is False:
        await ctx.send(f'"{input_name.lower()}" is not in the database')
    else:
        if arg == "":
            await ctx.send('A quote was not provided, try `jamal help` for help')
        else:
            jamal_bot_database.add_quote(input_name.lower(), arg)
            await ctx.send(f'Added “{arg}” to {input_name.lower()}')


@jamal_bot.group(description='Remove a name and their quotes from the database')
async def remove(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('Missing required argument, try `jamal help remove` for help')


@remove.command(
    name='name',
    description='Remove a name and their quotes from the database')
@commands.has_any_role(
    int(os.getenv('ADMIN_ROLE_ID')),
    int(os.getenv('MOD_ROLE_ID')))
async def rm_name(ctx, input_name: str):
    if jamal_bot_database.check_name(input_name.lower()) is False:
        await ctx.send(f'"{input_name.lower()}" is not in the database')
    else:
        jamal_bot_database.remove_name(input_name.lower())
        await ctx.send(f'Removed "{input_name.lower()}" from the database')


@jamal_bot.command(description='Get a random quote and guess who said it')
async def quotes(ctx):
    name = jamal_bot_database.random_name()
    await ctx.send(f'Who said “{jamal_bot_database.get_quote(name)}”')

    try:
        guess = await jamal_bot.wait_for('message', timeout=6.0)
    except asyncio.TimeoutError:
        return await ctx.channel.send(
            f'TOOK TO LONG it was {name}')

    if (str(guess.content)).lower() == name:
        await ctx.channel.send(f'You got em <@{guess.author.id}>')
    else:
        await ctx.channel.send(f'<@{guess.author.id}> YOU\'RE WRONG‼ IT WAS {name.upper()}‼')


# {server_address} is optional
@jamal_bot.command(description='Get the status of a Minecraft server.')
async def status(ctx, server_address=os.getenv('DEFAULT_SERVER_ADDRESS')):
    server = JavaServer.lookup(server_address)

    try:
        status = await server.async_status()
        server_latency = round(status.latency, 2)
        status_embed = disnake.Embed(
           title=server_address,
           description=status.version.name,
           colour=disnake.Colour.green())

        status_embed.add_field(
            name='Description',
            value=f'```{status.description}```',
            inline=False)
        status_embed.add_field(
            name='Count',
            value=f'{status.players.online}/{status.players.max}',
            inline=True)
        try:
            query = await server.async_query()
            server_players = (", ".join(query.players.names))
            status_embed.add_field(
                name="Players",
                # Unicode blank prevents an empty "value"
                value=f'\u200b{server_players}',
                inline=True)
            status_embed.set_footer(
                text=f'Ping: {server_latency} ms')
            await ctx.send(embed=status_embed)

        except Exception:
            status_embed.set_footer(text=f'Ping: {server_latency} ms')
            await ctx.send(embed=status_embed)

    except Exception:
        error_embed = disnake.Embed(
           title='Could not contact server',
           colour=disnake.Colour.red())
        await ctx.send(embed=error_embed)


@jamal_bot.command(description='Get the current time in different timezones')
async def time(ctx):
    timezone_UTC = pytz.utc
    timezone_EL = pytz.timezone('Europe/London')
    timezone_ET = pytz.timezone('US/Eastern')
    timezone_CT = pytz.timezone('US/Central')
    timezone_PT = pytz.timezone('US/Pacific')
    datetime_UTC = datetime.now(timezone_UTC)
    datetime_EL = datetime.now(timezone_EL)
    datetime_ET = datetime.now(timezone_ET)
    datetime_CT = datetime.now(timezone_CT)
    datetime_PT = datetime.now(timezone_PT)

    time_embed = disnake.Embed(colour=disnake.Colour.purple())
    time_embed.set_author(name='jamal bot time')
    time_embed.add_field(
        name='Universal',
        value=datetime_UTC.strftime('%b %d %I:%M %p (%H:%M)'),
        inline=False)
    time_embed.add_field(
        name='Europe/London',
        value=datetime_EL.strftime('%b %d %I:%M %p (%H:%M)'),
        inline=False)
    time_embed.add_field(
        name='US/Eastern',
        value=datetime_ET.strftime('%b %d %I:%M %p (%H:%M)'),
        inline=False)
    time_embed.add_field(
        name='US/Central',
        value=datetime_CT.strftime('%b %d %I:%M %p (%H:%M)'),
        inline=False)
    time_embed.add_field(
        name='US/Pacific',
        value=datetime_PT.strftime('%b %d %I:%M %p (%H:%M)'),
        inline=False)

    await ctx.send(embed=time_embed)


jamal_bot.run(os.getenv('DISCORD_API_KEY'))
