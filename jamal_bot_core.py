#        __                          __       ____          __
#       / /____ _ ____ ___   ____ _ / /      / __ ) ____   / /_
#  __  / // __ `// __ `__ \ / __ `// /      / __  |/ __ \ / __/
# / /_/ // /_/ // / / / / // /_/ // /      / /_/ // /_/ // /_
# \____/ \__,_//_/ /_/ /_/ \__,_//_/______/_____/ \____/ \__/
#                                 /_____/

import asyncio
import logging

import discord
import jamal_bot_config
import jamal_bot_database

from discord.ext import commands

# Recommended logging in discord.py documention
logging.basicConfig(level=logging.INFO)

# log to jamal_bot.log
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(
    filename='jamal_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
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
                         owner_id=jamal_bot_config.user_config['OWNER_ID'])
jamal_bot.remove_command('help')  # remove the default help command


@jamal_bot.event  # jamal connection to discord api
async def on_ready():
    print(f'\nLogged in as: {jamal_bot.user.name} - {jamal_bot.user.id}')
    print('Discord.py Version:', discord.__version__)
    activity = discord.Game(name='Warframe')
    await jamal_bot.change_presence(status=discord.Status.online,
                                    activity=activity)
    print('Done')  # Printing done let's pterodactyl know that it's ready


@jamal_bot.event  # jamal error handling
@commands.guild_only()  # ignore in DMs
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing required argument, try `jamal help` for help')


# jamal list
# ignore in DMs
@jamal_bot.command()
@commands.guild_only()
async def list(ctx):
    await ctx.send(f'{jamal_bot_database.get_names()}')


# jamal access {name}
# ignore in DMs
# set name to lowercase as that's how I like setting it up in the database
@jamal_bot.command()
@commands.guild_only()
async def access(ctx, name):
    name = name.lower()
    if jamal_bot_database.check_name(name) is True:
        if type(jamal_bot_database.get_quote(name)) is bool:
            await ctx.send(f'No quotes where found for {name}')
        else:
            await ctx.send(f'{jamal_bot_database.get_quote(name)}')
    else:
        await ctx.send(f'"{name}" is not in the database')


# jamal add name|quote {name} {*args}
# ignore in DMs
# must have admin role in order to add quotes
# admin role must be defined in config.yml
@jamal_bot.command()
@commands.guild_only()
@commands.has_any_role(jamal_bot_config.user_config['ADMIN_ROLE_ID'])
async def add(ctx, opt, name, *args):
    opt = opt.lower()

    if opt == "name":
        if jamal_bot_database.check_name(name) is True:
            await ctx.send(f'"{name}" is already in the database')
        else:
            jamal_bot_database.add_name(name)
            await ctx.send(
                f'{ctx.message.author.mention} has added '
                f'"{name}" to the database')

    elif opt == "quote":
        if jamal_bot_database.check_name(name) is False:
            await ctx.send(f'"{name}" is not in the database')
        else:
            words = []
            for arg in args:
                words.append(arg)
            quote = " ".join(words)

            if quote == "":
                await ctx.send('Quote cannot be empty, '
                               'try `jamal help` for help')
            else:
                jamal_bot_database.add_quote(name, quote)
                await ctx.send(
                    f'{ctx.message.author.mention} has added "{quote}" '
                    f'to {name}')


# jamal add {name} "{quote}"
# ignore in DMs
# must have admin role in order to remove names
@jamal_bot.command()
@commands.guild_only()
@commands.has_any_role(jamal_bot_config.user_config['ADMIN_ROLE_ID'])
async def remove(ctx, opt, name):
    opt = opt.lower()
    if opt == "name":
        if jamal_bot_database.check_name(name) is False:
            await ctx.send(f'"{name}" is not in the database')
        else:
            jamal_bot_database.remove_name(name)
            await ctx.send(
                f'{ctx.message.author.mention} has removed '
                '"{name}" from the database')


# jamal quotes
# ignores DMs
# random quote game command
# bot will send a random quote and it reads the next message as the guess
# wait 3 seconds for a guess before it timeouts
@jamal_bot.command()
@commands.guild_only()
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


# jamal help
# ignores DMs
# bot returns an easy to read embed explaining how to use the commands
@jamal_bot.command()
@commands.guild_only()
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
    await ctx.send(embed=help_embed)


# Run jamal_bot_core
jamal_bot.run(jamal_bot_config.user_config['DISCORD_API_KEY'], bot=True,
              reconnect=True)
