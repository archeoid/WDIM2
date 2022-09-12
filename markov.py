import random

def init(n):
    p = {}
    p[None] = n
    return p

def process(p, lines):
    for l in lines:
        append(p, l)

def tokenize(n, line):
    spans = []
    tokens = [t for t in line.split() if t]
    tokens = ["^"] + tokens + ["$"]
    
    for i in range(len(tokens)):
        span = []
        for j in range(min(n, len(tokens)-i)):
            span += [tokens[i+j]]
            if j:
                spans += [[i for i in span]]

    return spans

def append(p, line):
    n = p[None]
    for t in tokenize(n, line):
        a = ' '.join(t[:-1]).lower()
        b = t[-1]
        if not a in p:
            p[a] = []
        p[a] += [b]

def delete(p, token):
    for a in p:
        p[a] = [t for t in p[a] if t != token]

def generate(p, n = None):
    if not n:
        n = p[None]
    tokens = ["^"]
    while True:
        a = ' '.join(tokens[-min(len(tokens), n-1):]).lower()        
        b = random.choice(p[a])
        tokens += [b]
        if b == "$":
            break
        
    return ' '.join(tokens[1:-1])

def diminishing(n):
    weightings = []
    w = 0.5
    for i in range(n):
        weightings += [w]
        if i != n-2:
            w /= 2
    return weightings

def analysis(p, line):
    n = p[None]
    scores = [0]*(n-1)
    totals = [0]*(n-1)

    for t in tokenize(n, line):
        j = len(t)-2
        a = ' '.join(t[:-1]).lower()
        b = t[-1]
        if b == "$":
            continue
        
        if a in p and b in p[a]:
            scores[j] += 1
        totals[j] += 1

    score = scores[0]/totals[0]

    ln = 0
    for i in range(len(totals)):
        if totals[i] == 0:
            break
        ln += 1
    
    if ln > 1:
        score = 0
        weightings = diminishing(ln)
        for i in range(ln):
            score += (scores[i]/totals[i]) * weightings[i]

    return score