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

import discord
import pytz
from discord.ext import commands
from dotenv import load_dotenv
from mcstatus import MinecraftServer

import jamal_bot_database

# load environment variables from .env
load_dotenv()

# Recommended logging in discord.py documention
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# log to jamal_bot.log
logfilename = 'jamal_bot_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.log'
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=logfilename, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# in summary allow users to @mention the bot and use three different cased
# variations of "jamal " with a space
def get_prefix(client, message):
    prefixes = ['jamal ', 'Jamal ', 'JAMAL ']
    return commands.when_mentioned_or(*prefixes)(client, message)


# only creates the database if it doesn't exist
jamal_bot_database.create_db('jamal_bot_quotes.db')

# requires jamal with a space in order to register
jamal_bot = commands.Bot(command_prefix=get_prefix,
                         case_insensitive=True,
                         )
# remove the default help command
jamal_bot.remove_command('help')


# jamal connection to discord api
@jamal_bot.event
async def on_ready():
    print(f'\nLogged in as: {jamal_bot.user.name} - {jamal_bot.user.id}')
    print('Discord.py Version:', discord.__version__)
    activity = discord.Game(name='Warframe')
    await jamal_bot.change_presence(status=discord.Status.online,
                                    activity=activity)
    # Printing done let's pterodactyl know that it's ready
    print('Done')


# ignore in DMs
@jamal_bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


# jamal error handling
@jamal_bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required argument, try `jamal help` for help')


# jamal list
# ignore in DMs
@jamal_bot.command()
async def list(ctx):
    await ctx.send(f'{jamal_bot_database.get_names()}')


# jamal access {name}
# set name to lowercase as that's how I like setting it up in the database
@jamal_bot.command()
async def access(ctx, name):
    name = name.lower()
    if jamal_bot_database.check_name(name) is True:
        await ctx.send(f'{jamal_bot_database.get_quote(name)}')
    else:
        await ctx.send(f'"{name}" is not in the database')


# jamal add name|quote {name} {*args}
# must have admin role in order to add quotes
# admin role must be defined in config.yml
@jamal_bot.command()
@commands.has_any_role(os.getenv('ADMIN_ROLE_ID'))
async def add(ctx, opt, name, *args):
    opt = opt.lower()
    name = name.lower()

    if opt == "name":
        if jamal_bot_database.check_name(name) is True:
            await ctx.send(f'"{name}" is already in the database')
        else:
            jamal_bot_database.add_name(name)
            await ctx.send(
                f'{ctx.message.author.mention} has added "{name}" to the database')

    elif opt == "quote":
        if jamal_bot_database.check_name(name) is False:
            await ctx.send(f'"{name}" is not in the database')
        else:
            words = []
            for arg in args:
                words.append(arg)
            quote = " ".join(words)

            if quote == "":
                await ctx.send('Quote cannot be empty, try `jamal help` for help')
            else:
                jamal_bot_database.add_quote(name, quote)
                await ctx.send(
                    f'{ctx.message.author.mention} has added "{quote}" to {name}')
    else:
        raise discord.ext.commands.MissingRequiredArgument


# jamal remove {name}
# ignore in DMs
# must have admin role in order to remove names
@jamal_bot.command()
@commands.has_any_role(os.getenv('ADMIN_ROLE_ID'))
async def remove(ctx, opt, name):
    opt = opt.lower()
    name = name.lower()

    if opt == "name":
        if jamal_bot_database.check_name(name) is False:
            await ctx.send(f'"{name}" is not in the database')
        else:
            jamal_bot_database.remove_name(name)
            await ctx.send(
                f'{ctx.message.author.mention} has removed '
                '"{name}" from the database')
    else:
        raise discord.ext.commands.MissingRequiredArgument


# jamal quotes
# random quote game command
# bot will send a random quote and it reads the next message as the guess
# wait 3 seconds for a guess before it timeouts
@jamal_bot.command()
async def quotes(ctx, pass_context=True):
    name = jamal_bot_database.random_name()
    await ctx.send(f'who said "{jamal_bot_database.get_quote(name)}"')

    try:
        guess = await jamal_bot.wait_for('message', timeout=6.0)
    except asyncio.TimeoutError:
        return await ctx.channel.send(
            f'you\'re taking too long, it was {name}')

    if (str(guess.content)).lower() == name:
        await ctx.channel.send('you got em')
    else:
        await ctx.channel.send(f'WRONG! it\'s {name}')


# jamal status {server_address}
# {server_address} is optional
# ignore in DMs
@jamal_bot.command()
async def status(
    ctx,
    server_address=os.getenv('DEFAULT_SERVER_ADDRESS')
):
    server = MinecraftServer.lookup(server_address)

    try:
        status = server.status()
        server_latency = round(status.latency, 2)
        status_embed = discord.Embed(
           title=server_address,
           description=status.version.name,
           colour=discord.Colour.green())

        status_embed.add_field(
            name='Description',
            value=f'```{status.description}```',
            inline=False)
        status_embed.add_field(
            name='Count',
            value=f'{status.players.online}/{status.players.max}',
            inline=True)
        try:
            query = server.query()
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
        error_embed = discord.Embed(
           title='Could not contact server',
           colour=discord.Colour.red())
        await ctx.send(embed=error_embed)


# jamal time
# bot returns an easy to read embed displaying different timezones
@jamal_bot.command()
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

    time_embed = discord.Embed(colour=discord.Colour.purple())
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


# jamal help
# bot returns an easy to read embed explaining how to use the commands
@jamal_bot.command()
async def help(ctx):
    help_embed = discord.Embed(colour=discord.Colour.blurple())
    help_embed.set_author(name='jamal bot help')
    help_embed.add_field(
        name='Display this help message',
        value='Usage: `jamal help`',
        inline=False)
    help_embed.add_field(
        name='Display all available names in the database',
        value='Usage: `jamal list`',
        inline=False)
    help_embed.add_field(
        name='Send a random quote and guess who said it',
        value='Usage: `jamal quotes`',
        inline=False)
    help_embed.add_field(
        name='Send a random quote from someone',
        value='Usage: `jamal access <name>`\nEx. `jamal access kevin`',
        inline=False)
    help_embed.add_field(
        name='Add a name to the database',
        value='Usage: `jamal add name <name>`\nEx. `jamal add name kevin`',
        inline=False)
    help_embed.add_field(
        name='Add a quote to the database',
        value='Usage: `jamal add quote <name> <quote>`'
              '\nEx. `jamal add quote kevin she said give me armor`',
        inline=False)
    help_embed.add_field(
        name='Remove a name and their quotes from the database',
        value='Usage: `jamal remove name <name>`'
              '\nEx. `jamal remove name kevin`',
        inline=False)
    help_embed.add_field(
        name='Display the status of a minecraft server',
        value='Usage: `jamal status [address]`'
              '\nEx. `jamal status hypixel.net`',
        inline=False)
    help_embed.add_field(
        name='Display the time in different regions',
        value='Usage: `jamal time`',
        inline=False)
    await ctx.send(embed=help_embed)


# Run jamal_bot_core
jamal_bot.run(os.getenv('DISCORD_API_KEY'),
              bot=True,
              reconnect=True)
