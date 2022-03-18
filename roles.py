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
    #only respond to admins
    if not request.author.guild_permissions.manage_roles:
        return "Unauthorized. This incident will be reported"

    #command only works when replying to a message (the target)
    if not request.reference:
        return "Invalid use"

    input = request.content.removeprefix('.roles').strip().lower()

    if input == "clear":
        return await on_clear(request)
    if input == "dump":
        return await on_dump(request)
    
    return await on_map(request, input.split())   

async def on_map(request, parameters):

    #dont accept zero or odd number of arguments (must be emoji/role pairs!) 
    if not parameters or len(parameters) % 2 != 0:
        return "Invalid use"

    #make sure the message reference is valid
    reference = request.reference.resolved
    if not reference or type(reference) != discord.Message:
        return "Invalid use"
    
    pairs = [(parameters[i], parameters[i+1]) for i in range(0,len(parameters),2)]

    processed = []

    #extract the role and emoji ID (if applicable)
    for raw_emoji, raw_role in pairs:
        emoji = raw_emoji
        if match := DISCORD_EMOJI_REGEX.fullmatch(emoji):
            emoji = match.group(1) #extract the emoji ID
        elif match := UNICODE_EMOJI_REGEX.fullmatch(emoji):
            pass
        else:
            return f"`{emoji}` is not an emoji!"

        role = raw_role
        if match := DISCORD_ROLE_REGEX.fullmatch(role):
            role = match.group(1) #extract the role ID
        else:
            return f"`{role}` is not a role!"

        processed += [{'emoji': emoji, 'role':role, 'raw_emoji': raw_emoji}]

    message_id = str(request.reference.message_id)


    #now store the mappings
    if not db.get(message_id):
        db.dcreate(message_id)

    for m in processed:
        db.dadd(message_id, (m['emoji'], m['role']))
        #add a reaction to the message (saves the admins having too)
        await reference.add_reaction(m['raw_emoji'])

    #write to disk
    db.dump()
    
    #finally, acknowledge the command
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

async def on_dump(request):
    message_id = str(request.reference.message_id)
    
    output = ""

    if db.get(message_id):
        map = db.dgetall(message_id)
        for emoji, role in map.items():
            if emoji.isdecimal():
                emoji = f"<:emoji:{emoji}>"

            output += f"{emoji} <@&{role}>\n"
    else:
        output = "No roles mapped to this message"
    
    return output

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