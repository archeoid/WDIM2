import discord
import wdim
import roles
import mcrib
import nonsense
import flip
import questions
import random
import time
import re

WDIM_REGEX = re.compile("^\.(wc|wdim)\s*(?P<parameters>.*)$")

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

    a = discord.Activity(type=discord.ActivityType.watching, name="for weakness")
    await client.change_presence(status=discord.Status.online, activity=a)

    await nonsense.initialize(client)

@client.event
async def on_message(request):
    if type(request.channel) == discord.DMChannel: #respond to dms
        if request.author != client.user:
            await request.reply(content=nonsense.generate_nonsense())
        return
    
    if type(request.channel) != discord.TextChannel: #ignore unknown channels
        return
        
    if type(request.author) != discord.member.Member: #ignore non guild users
        return

    if request.author != client.user:
        await nonsense.process_message(request)
    
    reply = None

    command = request.content.lower()

    if m := WDIM_REGEX.fullmatch(command):
        params = m.group('parameters')
        async with request.channel.typing():
            reply = await wdim.on_wdim(request, params, client)
    elif command.startswith('.help'):
        reply = f"```\n{help}```"
    elif command.startswith('.mcrib'):
        async with request.channel.typing():
            reply = await mcrib.on_mcrib(request)
    elif command.startswith('.nonsense'):
        reply = await nonsense.on_nonsense(request, client)
    elif command.startswith('.flip'):
        reply = await flip.flip_coin(request)
    elif request.author != client.user and command.startswith('.roles'): #dont let it call privileged commands
        reply = await roles.on_command(request)
    elif client.user in request.mentions:
        reply = await questions.choose_answer(request)
        if not reply:
            await nonsense.respond(request, client)
    else:
        await nonsense.respond(request, client)
    
    if reply:
        await request.reply(reply)

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
