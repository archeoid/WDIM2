import re
import discord
import random

PREFIX_REGEX = re.compile("^[^:,]+[:,]")
STRICT_PREFIX_REGEX = re.compile("^[^:]+[:]")
POSTFIX_REGEX = re.compile("or ([^?]+)\?\s*$")
TERMS_REGEX = re.compile("([^,]+)")
MENTIONS_REGEX = re.compile("<@\d+>")

def decompose(query):
    query = query.content

    # remove all mentions from message content
    mentions = MENTIONS_REGEX.findall(query)  
    for mention in mentions:
        query = query.replace(mention, "")

    query = query.strip()

    tail = POSTFIX_REGEX.search(query)
    if not tail:
        terms = None
    
    else:
        query = POSTFIX_REGEX.sub("", query)

        if ':' in query:
            query = STRICT_PREFIX_REGEX.sub("", query)
        
        query = PREFIX_REGEX.sub("", query)

        terms = []
        for term in TERMS_REGEX.findall(query):
            if term := term.strip():
                terms += [term]
        terms += [tail.group(1).strip()]

    return terms

async def choose_answer(query):
    answers = decompose(query)
    if answers is None:
        raise discord.DiscordException("fucked shit")

    else:
        ans = random.choice(answers)

    prefixes = ["Hmm... I think you should go with ", "Definitely ", "Are you stupid? Obviously ", "Riblin says ", "", "If Zuko were here, he'd pick "]
    postfixes = [".", " for sure", "!", ", yeah"]

    return f"{random.choice(prefixes)}{ans}{random.choice(postfixes)}"