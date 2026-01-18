import sys
import worklang.lexer

with open(sys.argv[1]) as inputf:
    data = inputf.read()

tokens = worklang.lexer.Lexer().run(data)

print(tokens)