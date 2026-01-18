import sys
import worklang.lexer
import worklang.parser

with open(sys.argv[1]) as inputf:
    data = inputf.read()

tokens = worklang.lexer.Lexer().run(data)

print(tokens)

ast = worklang.parser.Parser().run(tokens)

print(ast)