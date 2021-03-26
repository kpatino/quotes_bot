#       __                          __       ____          __        ______
#      / /____ _ ____ ___   ____ _ / /      / __ ) ____   / /_      / ____/____   _____ ___
# __  / // __ `// __ `__ \ / __ `// /      / __  |/ __ \ / __/     / /    / __ \ / ___// _ \
# / /_/ // /_/ // / / / / // /_/ // /      / /_/ // /_/ // /_      / /___ / /_/ // /   /  __/
# \____/ \__,_//_/ /_/ /_/ \__,_//_/______/_____/ \____/ \__/______\____/ \____//_/    \___/
#                                 /_____/                  /_____/
# By Kevin Patino

import asyncio
import logging
import random
import sqlite3
import yaml

import discord
from discord.ext import commands

config_dict = {}

with open('config.yaml') as config:
    config_dict = yaml.load(config)
    print(config_dict)


# Recommended logging in discord.py documention
logging.basicConfig(level=logging.INFO)

# log to jamal_bot.log
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='jamal_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def get_prefix(client, message):  # Function creates prefixes
    # sets the prefixes, future regex here?
    prefixes = ['jamal ', 'Jamal ', 'JAMAL ']
    return commands.when_mentioned_or(*prefixes)(client, message)
    # in summary allow users to @mention the bot and use three variations of "jamal "


# requires jamal with a space in order to register
jamal_bot = commands.Bot(command_prefix=get_prefix,
                         case_insensitive=True, owner_id=config_dict['OWNER_ID'])
jamal_bot.remove_command('help')  # remove the default help command

# jamal_bot commands


@jamal_bot.event  # jamal connection to discord api
async def on_ready():
    print(
        f'\nLogged in as: {jamal_bot.user.name} - {jamal_bot.user.id}')
    print(
        f'Version: {discord.__version__}')
    activity = discord.Game(name='Warframe')
    await jamal_bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Done')  # Printing done let's pterodactyl know that it's ready


@jamal_bot.event  # jamal error handling
@commands.guild_only()  # ignore in DMs
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing required argument')


@jamal_bot.command()  # jamal lookup
@commands.guild_only()  # ignore in DMs
async def lookup(ctx):
    await ctx.send(f'{get_names()}')


@jamal_bot.command()  # jamal access {name}
@commands.guild_only()  # ignore in DMs
async def access(ctx, name):
    name = name.lower()  # set name to lowercase just in case
    if check_name(name) == True:  # check if the name is in the database
        await ctx.send(f'{get_quote(name)}')
    else:
        await ctx.send(f'"{name}" is not in the database')


@jamal_bot.command()  # jamal add {name} "{quote}"
@commands.guild_only()  # ignore in DMs
# must have these roles in order to add quotes
@commands.has_any_role(config_dict['ADMIN_ROLE_ID'])
async def add(ctx, name, quote: str):
    name = name.lower()  # set name to lowercase just in case
    if check_name(name) == False:  # check if name is in the database
        await ctx.send(f'"{name}" is not in the database')
    else:
        add_quote(name, quote)  # add_quote function
        # mention the author and send quote with name, reports this section has run
        await ctx.send(f'{ctx.message.author.mention} has added "{quote}" to {name}')


@jamal_bot.command()  # random quote game
@commands.guild_only()  # ignore in DMs
async def quotes(ctx, pass_context=True):
    name = random_name()
    await ctx.send(f'who said "{get_quote(name)}"')

    try:
        # wait 3 seconds for a guess
        guess = await jamal_bot.wait_for('message', timeout=6.0)
    except asyncio.TimeoutError:
        # if no guess is provided in 5 seconds stop waiting
        return await ctx.channel.send(f'you\'re taking too long, it was {name}')

    if (str(guess.content)).lower() == name:  # if guess matches namme
        await ctx.channel.send('you got em')
    else:
        await ctx.channel.send(f'WRONG! it\'s {name}')


@jamal_bot.command()  # jamal help
@commands.guild_only()  # ignore in DMs
async def help(ctx):
    help_embed = discord.Embed(colour=discord.Colour.blurple())
    help_embed.set_author(name='jamal help')
    help_embed.add_field(
        name='jamal help', value='jamal will display the help message', inline=False)
    help_embed.add_field(
        name='jamal lookup', value='jamal will display all available names in the database', inline=False)
    help_embed.add_field(
        name='jamal quotes', value='jamal will give a random quote and you guess who said it', inline=False)
    help_embed.add_field(name='jamal access <name>',
                         value='jamal will send a random quote from someone in the database', inline=False)
    help_embed.add_field(name='jamal add <name> "<quote>"',
                         value='jamal will add a quote to the database, but use the double quotes when you\'re adding new ones please', inline=False)
    help_embed.set_footer(
        text='more info at https://github.com/kpatino/jamal_bot/wiki')
    await ctx.send(embed=help_embed)  # actually send the embed

# database funtions
# SQLITE class and funtions


class open_db(object):  # sqlite ctx manager
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()


def get_names():
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names = [
            v[0] for v in cursor.fetchall()
        ]
        names = ', '.join(map(str, names,))
        return(names)


def add_name(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("INSERT INTO people ('name') VALUES (?)", (name,))


def remove_name(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("DELETE FROM people WHERE name == (?);", (name,))


def check_name(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("SELECT count(name) FROM people WHERE name=?", (name,))
        if cursor.fetchone()[0] == 1:
            return(True)
        else:
            return(False)


def get_quote(name):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT quote FROM quotes WHERE name=? ORDER BY RANDOM() LIMIT 1", (name,))
        return(cursor.fetchone()[0])


def add_quote(name, quote):
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "INSERT INTO quotes ('name', 'quote') VALUES (?, ?)", (name, quote, ))


def random_name():
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            "SELECT name FROM people")
        names = [
            v[0] for v in cursor.fetchall()
        ]
        name = random.choice(names)
        return(name)


# Run jamal_bot_core
jamal_bot.run(config_dict['DISCORD_API_KEY'], bot=True,
              reconnect=True)
