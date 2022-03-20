import discord
import wdim
import roles
import mcrib

import random
import time

client_intents = discord.Intents()
client_intents.guilds = True
client_intents.members = True
client_intents.messages = True
client_intents.guild_messages = True
client_intents.guild_reactions = True

client = discord.Client(intents = client_intents)

random.seed(time.time())
wdim.initialize()

token = ""
with open('token.txt') as f:
    token = f.read()

help = ""
with open('help.txt') as f:
    help = f.read()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    a = discord.Activity(type=discord.ActivityType.watching, name="👀")
    g = discord.Game("Elden Ring")
    await client.change_presence(status=discord.Status.online, activity=g)

@client.event
async def on_message(request):
    if request.author == client.user:
        return
    if type(request.author) != discord.member.Member: #ignore dm's
        await request.channel.send("https://tenor.com/view/kermit-awkward-smile-gif-14338677")
        return
    if type(request.channel) != discord.TextChannel: #ignore dm's again (you never know!)
        return
    
    error = None

    command = request.content.lower()

    if command.startswith('.wdim') or command.startswith('.wc'):
        async with request.channel.typing():
            error = await wdim.on_wdim(request, client)
    
    if command.startswith('.roles'):
        error = await roles.on_command(request)

    if command.startswith('.help'):
        error = f"```\n{help}```"

    if command.startswith('.mcrib'):
        error = await mcrib.on_mcrib(request)

    if error:
        await request.reply(error)

@client.event
async def on_raw_reaction_add(payload):
    guild_id = payload.guild_id
    user_id = payload.user_id

    if user_id == client.user.id:
        return #dont respond to our own reacts

    if not guild_id:
        return #ignore DM reacts

    member = client.get_guild(guild_id).get_member(user_id)
    error = await roles.on_reaction_add(payload, member)
    if error: print(error)


@client.event
async def on_raw_reaction_remove(payload):
    guild_id = payload.guild_id
    user_id = payload.user_id

    if user_id == client.user.id:
        return #dont respond to our own reacts

    if not guild_id:
        return #ignore DM reacts

    member = client.get_guild(guild_id).get_member(user_id)
    error = await roles.on_reaction_remove(payload, member)
    if error: print(error)

client.run(token)