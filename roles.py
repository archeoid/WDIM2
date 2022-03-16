import discord
import re
import emoji
import pickledb
import random

UNICODE_EMOJI_REGEX = emoji.get_emoji_regexp()
DISCORD_EMOJI_REGEX = re.compile("<a?:[^:]+:(\d+)>")
DISCORD_ROLE_REGEX = re.compile("<@&(\d+)>")
FEEDBACK_EMOJI = ["✊", "🙏", "👏", "🤝", "🤏", "😼"]

db = pickledb.load('roles.db', False)

async def on_command(request):
    if not request.author.guild_permissions.manage_roles:
        return "Unauthorized. This incident will be reported"

    if not request.reference:
        return "Invalid use"

    input = request.content.removeprefix('.roles').strip()

    if input.lower() == "clear":
        return await on_clear(request)
    
    return await on_map(request, input.split())   

async def on_map(request, parameters):   
    if len(parameters) != 2:
        return "Invalid use"

    emoji = parameters[0]
    if match := DISCORD_EMOJI_REGEX.fullmatch(emoji):
        emoji = match.group(1)
    elif match := UNICODE_EMOJI_REGEX.fullmatch(emoji):
        emoji = emoji
    else:
        return "Not an emoji"

    role = parameters[1]
    if match := DISCORD_ROLE_REGEX.fullmatch(role):
        role = match.group(1)
    else:
        return "Not a role"
    
    message_id = str(request.reference.message_id)

    reference = request.reference.resolved

    if reference and type(reference) == discord.Message:
        await reference.add_reaction(parameters[0])


    if not db.get(message_id):
        db.dcreate(message_id)
    db.dadd(message_id, (emoji, role))
    db.dump()
    
    await request.add_reaction(random.choice(FEEDBACK_EMOJI))
    return

async def on_clear(request):
    message_id = str(request.reference.message_id)
    if db.get(message_id):
        db.drem(message_id)
        db.dump()
    else:
        return "Nothing to clear"

    await request.add_reaction(random.choice(FEEDBACK_EMOJI))

def lookup_role(payload, member):
    message_id = str(payload.message_id)

    if not db.get(message_id):
        return None #message has no registered roles

    emoji = payload.emoji.id
    if not emoji: #no ID means a unicode emoji
        emoji = payload.emoji.name
    emoji = str(emoji)

    if not db.dexists(message_id, emoji):
        return None #message doesnt have this emoji registered

    #get role ID from the DB
    role = db.dget(message_id, emoji)

    #get guild role from ID
    role = member.guild.get_role(int(role))
    
    return role

async def on_reaction_add(payload, member):
    role = lookup_role(payload, member)

    if not role:
        return
    
    try:
        await member.add_roles(role)
    except discord.Forbidden:
        return f"forbidden"

    return None

async def on_reaction_remove(payload, member):
    role = lookup_role(payload, member)

    if not role:
        return
    
    try:
        await member.remove_roles(role)
    except discord.Forbidden:
        return f"forbidden"

    return None