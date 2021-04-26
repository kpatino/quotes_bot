#       __                          __       ____          __        ______
#      / /____ _ ____ ___   ____ _ / /      / __ ) ____   / /_      / ____/____   _____ ___
# __  / // __ `// __ `__ \ / __ `// /      / __  |/ __ \ / __/     / /    / __ \ / ___// _ \
# / /_/ // /_/ // / / / / // /_/ // /      / /_/ // /_/ // /_      / /___ / /_/ // /   /  __/
# \____/ \__,_//_/ /_/ /_/ \__,_//_/______/_____/ \____/ \__/______\____/ \____//_/    \___/
#                                 /_____/                  /_____/
#

import asyncio
import logging

import discord
from discord.ext import commands

import jamal_bot_config
import jamal_bot_database

# Recommended logging in discord.py documention
logging.basicConfig(level=logging.INFO)

# log to jamal_bot.log
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='jamal_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def get_prefix(client, message):  # Function creates prefixes
    # sets the prefixes, future regex here?
    prefixes = ['jamal ', 'Jamal ', 'JAMAL ']
    return commands.when_mentioned_or(*prefixes)(client, message)
    # in summary allow users to @mention the bot and use three variations of "jamal "


# requires jamal with a space in order to register
jamal_bot = commands.Bot(command_prefix=get_prefix,
                         case_insensitive=True,
                         owner_id=jamal_bot_config.user_config['OWNER_ID'])
jamal_bot.remove_command('help')  # remove the default help command

# jamal_bot commands


@jamal_bot.event  # jamal connection to discord api
async def on_ready():
    print(f'\nLogged in as: {jamal_bot.user.name} - {jamal_bot.user.id}')
    print('Discord.py Version:', discord.__version__)
    activity = discord.Game(name='Warframe')
    await jamal_bot.change_presence(status=discord.Status.online, activity=activity)
    print('Done')  # Printing done let's pterodactyl know that it's ready


@jamal_bot.event  # jamal error handling
@commands.guild_only()  # ignore in DMs
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing required argument')


@jamal_bot.command()  # jamal list
@commands.guild_only()  # ignore in DMs
async def list(ctx):
    await ctx.send(f'{jamal_bot_database.get_names()}')


@jamal_bot.command()  # jamal access {name}
@commands.guild_only()  # ignore in DMs
async def access(ctx, name):
    # set name to lowercase as that's how I like setting it up in the database
    name = name.lower()
    if jamal_bot_database.check_name(name) is True:
        await ctx.send(f'{jamal_bot_database.get_quote(name)}')
    else:
        await ctx.send(f'"{name}" is not in the database')


@jamal_bot.command()  # jamal add name|quote {name} "{quote}"
@commands.guild_only()  # ignore in DMs
# must have admin role in order to add quotes
@commands.has_any_role(jamal_bot_config.user_config['ADMIN_ROLE_ID'])
async def add(ctx, var, name, quote: str = None):
    var = var.lower()  # set var to lowercase

    if var == "name":
        # check if name is in the database
        if jamal_bot_database.check_name(name) is True:
            await ctx.send(f'"{name}" is already in the database')
        else:
            jamal_bot_database.add_name(name)
            await ctx.send(f'{ctx.message.author.mention} has added "{name}" to the database')

    elif var == "quote":
        # check if name is in the database
        if jamal_bot_database.check_name(name) is False:
            await ctx.send(f'"{name}" is not in the database')
        else:
            jamal_bot_database.add_quote(name, quote)  # add_quote function
            # mention the author and send quote with name, reports this section has run
            await ctx.send(f'{ctx.message.author.mention} has added "{quote}" to {name}')


@jamal_bot.command()  # jamal add {name} "{quote}"
@commands.guild_only()  # ignore in DMs
# must have admin role in order to remove names
@commands.has_any_role(jamal_bot_config.user_config['ADMIN_ROLE_ID'])
async def remove(ctx, var, name):
    var = var.lower()  # set var to lowercase
    if var == "name":
        # check if name is in the database
        if jamal_bot_database.check_name(name) is False:
            await ctx.send(f'"{name}" is not in the database')
        else:
            jamal_bot_database.remove_name(name)
            await ctx.send(f'{ctx.message.author.mention} has removed "{name}" from the database')


@jamal_bot.command()  # random quote game
@commands.guild_only()  # ignore in DMs
async def quotes(ctx, pass_context=True):
    name = jamal_bot_database.random_name()
    await ctx.send(f'who said "{jamal_bot_database.get_quote(name)}"')

    try:
        # wait 3 seconds for a guess
        guess = await jamal_bot.wait_for('message', timeout=6.0)
    except asyncio.TimeoutError:
        # if no guess is provided in 3 seconds stop waiting
        return await ctx.channel.send(f'you\'re taking too long, it was {name}')

    if (str(guess.content)).lower() is name:  # if guess matches namme
        await ctx.channel.send('you got em')
    else:
        await ctx.channel.send(f'WRONG! it\'s {name}')


@jamal_bot.command()  # jamal help
@commands.guild_only()  # ignore in DMs
async def help(ctx):
    help_embed = discord.Embed(colour=discord.Colour.blurple())
    help_embed.set_author(name='jamal bot help')
    help_embed.add_field(name='Display this help message',
                         value='Usage: `jamal help`', inline=False)
    help_embed.add_field(name='Display all available names in the database',
                         value='Usage: `jamal list`', inline=False)
    help_embed.add_field(name='Send a random quote and guess who said it',
                         value='Usage: `jamal quotes`', inline=False)
    help_embed.add_field(name='Send a random quote from someone',
                         value='Usage: `jamal access <name>`\nEx. `jamal access kevin`', inline=False)
    help_embed.add_field(name='Add a name to the database',
                         value='Usage: `jamal add name <name>`\nEx. `jamal add name kevin`', inline=False)
    help_embed.add_field(name='Add a quote to the database, needs double quotes surrounding the quote',
                         value='Usage: `jamal add quote <name> "<quote>"`\nEx. `jamal add quote kevin "no pos guao"`', inline=False)
    help_embed.add_field(name='Remove a name and their quotes from the database',
                         value='Usage: `jamal remove name <name>`\nEx. `jamal remove name kevin`', inline=False)
    await ctx.send(embed=help_embed)  # actually send the embed


# Run jamal_bot_core
jamal_bot.run(jamal_bot_config.user_config['DISCORD_API_KEY'], bot=True,
              reconnect=True)
