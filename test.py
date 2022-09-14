import parse
import tree

query = "could you actually be online when people need you?"

derivation = parse.parse(query)

tree.render(query, derivation, "output.png")