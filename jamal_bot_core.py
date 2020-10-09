import asyncio
import random
import sqlite3

import discord
from discord.ext import commands
from mcstatus import MinecraftServer

# jamal
def get_prefix(client, message): # Function creates prefixes
    prefixes = ['jamal ', 'Jamal ', 'JAMAL '] # sets the prefixes, future regex here?
    return commands.when_mentioned_or(*prefixes)(client, message) 
    # in summary allow users to @mention the bot and use three variations of "jamal "

jamal_bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True,owner_id=199324290665938944) # requires jamal with a space in order to register
jamal_bot.remove_command('help') # remove the default help command

# jamal_bot commands
@jamal_bot.event # jamal connection to discord api
async def on_ready():
    print(print(f'\n\nLogged in as: {jamal_bot.user.name} - {jamal_bot.user.id}\nVersion: {discord.__version__}\n'))
    activity = discord.Game(name='Warframe') 
    await jamal_bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Successfully logged in and booted')

@jamal_bot.event # jamal error handling
@commands.guild_only() # ignore in DMs
async def on_command_error(ctx, error): 
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('what the fuck are you trying to ask')

@jamal_bot.command() # jamal lookup
@commands.guild_only() # ignore in DMs
async def lookup(ctx):
    await ctx.send(f'{list_tables()}')

@jamal_bot.command() # jamal access {name}
@commands.guild_only() # ignore in DMs
async def access(ctx, name):
    name = name.lower() # set name to lowercase just in case
    if check_tables(name) == True: # check if the name is in the database
        await ctx.send(f'{get_quote(name)}')
    else:
        await ctx.send(f'"{name}" is not in the database')

@jamal_bot.command() # jamal add {name} "{quote}"
@commands.guild_only() # ignore in DMs
@commands.has_any_role(ADD ROLE ID NUMBERS HERE IF APPLICABLE OR DELETE LINE) #must have these roles in order to add quotes
async def add(ctx, name, quote:str):
    name = name.lower() # set name to lowercase just in case
    if check_tables(name) == False: # check if name is in the database
        await ctx.send(f'"{name}" is not in the database')
    else:
        add_quote(name, quote) # add_quote function
        await ctx.send(f'<@199324290665938944>, {ctx.message.author.mention} has added "{quote}" to {name}') #mention me, the author and send quote with name, reports this section has run        

@jamal_bot.command() # random quote game
@commands.guild_only() # ignore in DMs
async def quotes(ctx, pass_context = True):
    name = random_table()
    await ctx.send(f'who said "{get_quote(name)}"')

    try: 
        guess = await jamal_bot.wait_for('message', timeout=6.0) #wait 3 seconds for a guess
    except asyncio.TimeoutError: 
        return await ctx.channel.send(f'you\'re dragging it was {name}') #if no guess is provided in 5 seconds stop waiting

    if (str(guess.content)).lower() == name: #if guess matches namme
        await ctx.channel.send('you got em')
    else:
        await ctx.channel.send(f'WRONG! it\'s {name}')

@jamal_bot.command() #jamal summon the {summonables_lookup}
@commands.guild_only() # ignore in DMs
async def summon(ctx, the, role, pass_context = True):
    the = the.lower() #set the to lower case in case some monkey capitalized it
    role = role.lower() #even bigger monkey if the capitalized gamer or council
    if the != 'the': #check if they used "the" otherwise return
        return
    elif role in summonables_lookup: #check if role is in summonables
        await ctx.send(f'{ctx.message.author.mention} has summoned the {summonables_lookup[role]}') #snitch on whoever summoned the council
    else:
        await ctx.send(f'"{role}" is not summonable') #if the role is not summonable

@jamal_bot.command() #jamal status {server_address}
@commands.guild_only() # ignore in DMs
async def status(ctx, server_address='minecraft.net'):
    try:
        await ctx.send(check_server_status(server_address))
    except:
        await ctx.send('Could not contact server')
    
@jamal_bot.command() # jamal mimic {ctx}
#@commands.guild_only()
async def mimic(ctx, channel_id, *, arg):
    channel = jamal_bot.get_channel(int(channel_id))
    await channel.send(arg)

@jamal_bot.command() #jamal help
@commands.guild_only() # ignore in DMs
async def help(ctx):
    help_embed = discord.Embed(colour = discord.Colour.blurple())
    help_embed.set_author(name='jamal help')
    help_embed.add_field(name='jamal help', value='jamal will display this message for your dumbass to read', inline=False)
    help_embed.add_field(name='jamal lookup', value='jamal will display all the names in the database', inline=False)
    help_embed.add_field(name='jamal quotes', value='jamal will give a quote and you guess who said it, it\'s simple', inline=False)
    help_embed.add_field(name='jamal access <name>', value='jamal will send a random quote from someone in the database', inline=False)
    help_embed.add_field(name='jamal add <name> "<quote>"', value='jamal will add a quote to the database, but use the fucking double quotes when you\'re adding new ones please', inline=False)
    help_embed.add_field(name='jamal status <server_address>', value='jamal by default will give the minetino status, otherwise provide a server', inline=False)
    help_embed.add_field(name='jamal summon the <council | gamers>', value='jamal will summon the council or the gamers, but at a cost', inline=False)
    help_embed.set_footer(text='commands are mostly case insensitive, try to always use lowercase just in case')
    await ctx.send(embed=help_embed) #actually send the embed

#Dictionaries, don't forget to add new entries to every dictionary
summonables_lookup = {
    "council":"<@&>",
    "gamers":"<@&>",
    }
    
#check minecraft server status
def check_server_status(address):
    server = MinecraftServer.lookup(address)
    status = server.status()
    online_check = (f'The server has {status.players.online} players online and replied in {status.latency} ms')
    return(online_check)

#check minecraft server players
def check_server_players(address):
    server = MinecraftServer.lookup(address)
    query = server.query()
    player_check = "{0}".format(", ".join(query.players.names))
    return(player_check)

#database funtions
#SQLITE class and funtions
# Context manager opens and closes database, don't want to leave open connections
class open_db(object): # sqlite ctx manager i found on github, seems to work for now
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
        cursor.execute("""SELECT name FROM sqlite_master WHERE type='table';""")
        tables = [
            v[0] for v in cursor.fetchall()
            if v[0] != "sqlite_sequence"
            ]
        tables = ', '.join(map(str, tables,)) 
        return(tables)

def check_tables(table): #check if the table exists to prevent a crash
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(f"""SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table}';""")
        if cursor.fetchone()[0]==1: 
            return(True)
        else:
            return(False)

def get_quote(name): #get quote from database
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(f"""SELECT * FROM {name} ORDER BY RANDOM() LIMIT 1;""")
        return(cursor.fetchone()[0])

def add_quote(name, quote): #add quote to database
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute(f"""INSERT INTO {name} (quotes) VALUES("{quote}");""")

def random_table(): #get a random table
    with open_db('./jamal_bot_quotes.db') as cursor:
        cursor.execute("""SELECT name FROM sqlite_master WHERE type='table';""")
        tables = [
            v[0] for v in cursor.fetchall()
            if v[0] != "sqlite_sequence"
            ]
        name = random.choice(tables)
        return(name)

jamal_bot.run("DISCORD_API_KEY_HERE", bot=True, reconnect=True) #Run jamal_bot
