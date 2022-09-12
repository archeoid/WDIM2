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

def has_yesno(derivation, yesno):
    if not "daughters" in derivation:
        return

    if "yesno" in derivation['entity']:
        yesno[0] = True

    for d in derivation["daughters"]:
        has_yesno(d, yesno)

def case_transfer(s, query):
    i = query.lower().index(s.lower())
    return query[i:i+len(s)]

def find_options(query):
    options = []
    stdout = sys.stdout
    f = open('/dev/null', 'w')
    sys.stdout = f
    with ace.ACEParser('erg.dat', cmdargs=["-1"], tsdbinfo=True) as parser:
        
        response = parser.interact(query)
        derivation = response.result(0).derivation().to_dict(fields=('form', 'entity', 'daughters'))

        trees = []
        extract(derivation, trees)

        for t in trees:
            if "daughters" in t and all([d in trees for d in t["daughters"]]):
                continue
            s = []
            flatten(t, s)
            o = ' '.join(s)
            if o[-1] == ',' or o[-1] == '?':
                o = o[:-1]
            o = case_transfer(o, query)
            options += [o]

        if len(options) == 0:
            yesno = [False]
            has_yesno(derivation, yesno)
            if yesno[0]:
                options = ["yes", "no"]

    return options