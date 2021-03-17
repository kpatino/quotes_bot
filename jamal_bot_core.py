import asyncio
import logging
import random
import sqlite3

import discord
from discord.ext import commands

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
                         case_insensitive=True, owner_id="DISCORD_ID")
jamal_bot.remove_command('help')  # remove the default help command

# jamal_bot commands


@jamal_bot.event  # jamal connection to discord api
async def on_ready():
    print(print(
        f'\n\nLogged in as: {jamal_bot.user.name} - {jamal_bot.user.id}\nVersion: {discord.__version__}\n'))
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
    await ctx.send(f'{list_tables()}')


@jamal_bot.command()  # jamal access {name}
@commands.guild_only()  # ignore in DMs
async def access(ctx, name):
    name = name.lower()  # set name to lowercase just in case
    if check_tables(name) == True:  # check if the name is in the database
        await ctx.send(f'{get_quote(name)}')
    else:
        await ctx.send(f'"{name}" is not in the database')


@jamal_bot.command()  # jamal add {name} "{quote}"
@commands.guild_only()  # ignore in DMs
# must have these roles in order to add quotes
@commands.has_any_role("ROLE_ID")
async def add(ctx, name, quote: str):
    name = name.lower()  # set name to lowercase just in case
    if check_tables(name) == False:  # check if name is in the database
        await ctx.send(f'"{name}" is not in the database')
    else:
        add_quote(name, quote)  # add_quote function
        # mention the author and send quote with name, reports this section has run
        await ctx.send(f'{ctx.message.author.mention} has added "{quote}" to {name}')


@jamal_bot.command()  # random quote game
@commands.guild_only()  # ignore in DMs
async def quotes(ctx, pass_context=True):
    name = random_table()
    await ctx.send(f'who said "{get_quote(name)}"')

    try:
        # wait 3 seconds for a guess
        guess = await jamal_bot.wait_for('message', timeout=6.0)
    except asyncio.TimeoutError:
        # if no guess is provided in 5 seconds stop waiting
        return await ctx.channel.send(f'you\'re dragging it was {name}')

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
        name='jamal help', value='jamal will display this message for your dumbass to read', inline=False)
    help_embed.add_field(
        name='jamal lookup', value='jamal will display all the names in the database', inline=False)
    help_embed.add_field(
        name='jamal quotes', value='jamal will give a quote and you guess who said it, it\'s simple', inline=False)
    help_embed.add_field(name='jamal access <name>',
                         value='jamal will send a random quote from someone in the database', inline=False)
    help_embed.add_field(name='jamal add <name> "<quote>"',
                         value='jamal will add a quote to the database, but use the fucking double quotes when you\'re adding new ones please', inline=False)
    help_embed.set_footer(
        text='commands are mostly case insensitive, try to always use lowercase just in case')
    await ctx.send(embed=help_embed)  # actually send the embed

# database funtions
# SQLITE class and funtions
# Context manager opens and closes database, don't want to leave open connections


class open_db(object):  # sqlite ctx manager i found on github, seems to work for now
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()


def list_tables():
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            """SELECT name FROM sqlite_master WHERE type='table';""")
        tables = [
            v[0] for v in cursor.fetchall()
            if v[0] != "sqlite_sequence"
        ]
        tables = ', '.join(map(str, tables,))
        return(tables)


def check_tables(table):  # check if the table exists to prevent a crash
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            f"""SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table}';""")
        if cursor.fetchone()[0] == 1:
            return(True)
        else:
            return(False)


def get_quote(name):  # get quote from database
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(f"""SELECT * FROM {name} ORDER BY RANDOM() LIMIT 1;""")
        return(cursor.fetchone()[0])


def add_quote(name, quote):  # add quote to database
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(f"""INSERT INTO {name} (quotes) VALUES("{quote}");""")


def random_table():  # get a random table
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(
            """SELECT name FROM sqlite_master WHERE type='table';""")
        tables = [
            v[0] for v in cursor.fetchall()
            if v[0] != "sqlite_sequence"
        ]
        name = random.choice(tables)
        return(name)


jamal_bot.run("DISCORD_API_KEY_HERE", bot=True,
              reconnect=True)  # Run jamal_bot
