import sys
import worklang.lexer
import worklang.parser
import worklang.compiler
import worklang.tempvm

with open(sys.argv[1]) as inputf:
    data = inputf.read()

tokens = worklang.lexer.Lexer().run(data)

# print(tokens)

ast = worklang.parser.Parser().run(tokens)

# print(ast)

c = worklang.compiler.Compiler()
c.compile_module(ast)

bytecode = c.dump()

vm = worklang.tempvm.VM()
vm.load_from_bytes(bytecode)

vm.run("Главный", "$global")