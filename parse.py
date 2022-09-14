from delphin import ace
from delphin import derivation
import sys

def flatten(derivation, out):
    if "conj" in derivation["entity"]:
        return

    if not "daughters" in derivation:
        form = derivation["form"]
        out += [form]
        return

    for d in derivation["daughters"]:
        flatten(d, out)

def extract(derivation, interest):
    if not "daughters" in derivation:
        return

    if "crd" in derivation['entity']:
        interest += derivation["daughters"]

    for d in derivation["daughters"]:
        extract(d, interest)

def has_generic(derivation, generic):
    if "generic" in derivation['entity']:
        generic[0] = True

    if not "daughters" in derivation:
        return

    for d in derivation["daughters"]:
        has_generic(d, generic)

def has_yesno(derivation, yesno):
    if not "daughters" in derivation:
        return

    if "yesno" in derivation['entity']:
        yesno[0] = True

    for d in derivation["daughters"]:
        has_yesno(d, yesno)

def case_transfer(tokens, original):
    min_index = len(original)
    max_index = 0
    
    lower = original.lower()

    for t in tokens:
        start = lower.index(t.lower())
        end = start + len(t)

        if start < min_index:
            min_index = start
        
        if end > max_index:
            max_index = end

    return original[min_index:max_index]

def parse(query, allow_generic=True):
    if 'http' in query:
        return []

    derivation = {}

    with ace.ACEParser('erg.dat', cmdargs=["-1"], tsdbinfo=True) as parser:
        response = parser.interact(query)

        if len(response.results()) == 0:
            return []

        derivation = response.result(0).derivation().to_dict(fields=('form', 'entity', 'daughters'))

    if derivation and not allow_generic:
        generic = [False]
        has_generic(derivation, generic)
        if generic[0]:
            return []

    return derivation

def find_options(query, derivation):
    options = []
    trees = []

    extract(derivation, trees)

    for t in trees:
        if "daughters" in t and all([d in trees for d in t["daughters"]]):
            continue
        s = []
        flatten(t, s)
        
        if s[-1] == ',' or s[-1] == '?':
            s = s[:-1]
        
        o = case_transfer(s, query)
        options += [o]

    if len(options) == 0:
        yesno = [False]
        has_yesno(derivation, yesno)
        if yesno[0]:
            options = ["yes", "no"]

    return options