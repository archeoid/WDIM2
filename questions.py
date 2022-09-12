import re
import discord
import random
import parse

PREFIX_REGEX = re.compile("^[^:,?]+[:,?]")
STRICT_PREFIX_REGEX = re.compile("^[^:]+[:]")
POSTFIX_REGEX = re.compile("[\s,]or ([^?]+)\?\s*$")
OPTIONS_REGEX = re.compile("([^,]+)")
MENTIONS_REGEX = re.compile("<@\d+>")

PREFIXS = ["Hmm... I think you should go with ", "Definitely ", "Are you stupid? Obviously ", "Riblin says ", "", "If Zuko were here, he'd pick "]
POSTFIXS = [".", " for sure", "!", ", yeah"]

def find_options(query):
    query = query.content
    query = query.strip()

    # remove all mentions from message content
    mentions = MENTIONS_REGEX.findall(query)  
    for mention in mentions:
        query = query.replace(mention, "")

    # check for the naive "A or B", "A or B?"
    naive = query.split()
    if len(naive) == 3 and naive[1].lower() == "or":
        return [naive[0], naive[2].replace("?", "")]

    # try do proper parsing, fallback to regex
    options = parse.find_options(query)
    if options:
        return options
    

    # extract the "or ###?"
    tail = POSTFIX_REGEX.search(query)

    # no match, cannot parse
    if not tail:
        return []
    
    # remove tail
    query = POSTFIX_REGEX.sub("", query)


    # remove the prefix
    with_prefix = ""+query
    if ':' in query:
        query = STRICT_PREFIX_REGEX.sub("", query)
    query = PREFIX_REGEX.sub("", query)

    # no prefix so compromise, only extract the last token of the first option
    no_prefix = with_prefix == query

    # find all remaining options
    options = []
    for option in OPTIONS_REGEX.findall(query):
        if option := option.strip():
            options += [option]
    if no_prefix:
        options[0] = options[0].split()[-1]
    
    # add the tail option we removed
    options += [tail.group(1).strip()]

    return options

async def choose_answer(query):
    options = find_options(query)
    if not options:
        return None

    answer = random.choice(options)
    prefix = random.choice(PREFIXS)
    postfix = random.choice(POSTFIXS)

    return f"{prefix}{answer}{postfix}"