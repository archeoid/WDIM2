import random

def process(lines):
    p = {}

    for l in lines:
        append(p, l)

    return p

def append(p, line):
    if not "^" in p:
        p["^"] = []
    
    words = line.split()

    if len(words) == 0:
        return

    p["^"].append(words[0])

    for i in range(1, len(words)):
        last = words[i-1]
        key = last.lower()
        this = words[i]

        if not key in p:
            p[key] = []
        
        p[key].append(this.strip())

    last = words[-1].lower()
    if not last in p:
        p[last] = []
    
    p[last].append("$")

def generate(p):
    current = "^"
    out = ""
    while True:
        if not current.lower() in p:
            break
        current = random.choice(p[current.lower()])

        if current == "$":
            break

        if current in "!,?.":
            out = out[:-1]

        out += current + " "
    return out