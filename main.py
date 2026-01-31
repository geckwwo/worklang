import sys
import worklang.lexer
import worklang.parser
import worklang.compiler
import worklang.tempvm

with open(sys.argv[1]) as inputf:
    data = inputf.read()

tokens = worklang.lexer.Lexer().run(data)

# print(tokens)
parser = worklang.parser.Parser()
try:
    ast = parser.run(tokens)
except Exception as e:
    print(f"Parser error around token {parser.tok}")
    raise e from None
# print(ast)

c = worklang.compiler.Compiler()
c.compile_module(ast)

vfs = c.dump_vfs()

vm = worklang.tempvm.VM()
vm.add_modsource(worklang.tempvm.VirtualSource(vfs))

vm.load_module("Главный")