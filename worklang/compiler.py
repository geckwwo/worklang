from .parser import Node, CallNode, ConstNode, IdenNode, ModuleDeclNode, DiscardNode, BinOpNode, ProcDeclNode
from .lexer import TokenType
import struct
from dataclasses import dataclass

MAGIC = b"Wklg\00\01\02\03"

class Encoder:
    @classmethod
    def str(cls, s: str):
        encoded = s.encode()
        return cls.int32(len(encoded)) + encoded
    
    @classmethod
    def int32(cls, i: int):
        return i.to_bytes(4, "big")
    @classmethod
    def int16(cls, i: int):
        return i.to_bytes(2, "big")
    @classmethod
    def varint(cls, i: int):
        if i == 0:
            return bytearray([1, 0])
        b = i.to_bytes((i.bit_length() + 8) // 8, "big", signed=True)
        return bytearray([len(b), *b])

    @classmethod
    def float(cls, f: float):
        return struct.pack("f", f)

@dataclass
class RunnableEntry:
    args: list[str]
    bytecode: bytearray | bytes

class ConstEntry:
    INT = 1
    FLOAT = 2
    STRING = 3
    RUNNABLE = 4

class Opcodes:
    NOP = 0x00 # not used by compiler, but must be implemented in VM
    PUSH_CONST = 0x01

    GET = 0x0A
    SET_GLOBAL = 0x0B
    SET = 0x0C

    INVOKE = 0x10

    ADD = 0x20
    MULTIPLY = 0x21

    RETURN = 0x7F
    DISCARD = 0x80

CONST_TYPE = int | float | str | RunnableEntry

class Module:
    def __init__(self):
        self.name: str | None = None
        self.bytecode: bytearray | None = None
        self.const_pool: list[CONST_TYPE] = []
    
    def push_const(self, const: CONST_TYPE):
        if const in self.const_pool:
            return self.const_pool.index(const)
        self.const_pool.append(const)
        return len(self.const_pool) - 1

    def set_name(self, name: str):
        self.name = name
    def get_name(self):
        if self.name is None:
            raise ValueError("Modules should have a name!")
        return self.name
    
    def dump(self):
        assert self.bytecode is not None

        result = bytearray()

        result.extend(Encoder.str(self.get_name()))        
        result.extend(Encoder.int32(len(self.const_pool)))
        for entry in self.const_pool:
            if isinstance(entry, str):
                result.append(ConstEntry.STRING)
                result.extend(Encoder.str(entry))
            elif isinstance(entry, int):
                result.append(ConstEntry.INT)
                result.extend(Encoder.varint(entry))
            elif isinstance(entry, RunnableEntry):
                result.append(ConstEntry.RUNNABLE)
                result.append(len(entry.args))
                for i in entry.args:
                    result.extend(Encoder.str(i))
                result.extend(Encoder.int32(len(entry.bytecode)))
                result.extend(entry.bytecode)
            else:
                raise NotImplementedError(f"Cannot serialize const pool entry {entry}")

        result.extend(Encoder.int32(len(self.bytecode)))
        result.extend(self.bytecode)
        return result

class Compiler:
    def __init__(self):
        self.module_stack: list[Module] = []

        self.module_cache: dict[str, Module] = {}

    def compile_module(self, module_ast: list[Node]):
        self.module_stack.append(Module())
        bytecode = bytearray()

        for i in module_ast:
            bytecode.extend(self.visit_node(i))
        mod = self.module_stack.pop()

        assert mod.get_name() not in self.module_cache
        self.module_cache[mod.get_name()] = mod

        mod.bytecode = bytecode

        return mod

    def visit_node(self, node: Node) -> bytearray:
        return getattr(self, "visit_node_" + node.__class__.__name__, self.no_node_visitor)(node)
    def no_node_visitor(self, node: Node) -> bytearray:
        raise NotImplementedError(f"No visitor for node {node}")
    
    def visit_node_ProcDeclNode(self, node: ProcDeclNode):
        bytecode = bytearray()

        for i in node.body:
            bytecode.extend(self.visit_node(i))

        ptr_runnable = self.module_stack[-1].push_const(RunnableEntry(node.args, bytecode))
        ptr_name = self.module_stack[-1].push_const(node.name)

        return bytearray([Opcodes.PUSH_CONST, *Encoder.int32(ptr_runnable), Opcodes.SET, *Encoder.int32(ptr_name)])

    def visit_node_ModuleDeclNode(self, node: ModuleDeclNode):
        self.module_stack[-1].set_name(".".join(node.modname))
        return bytearray()

    def visit_node_CallNode(self, node: CallNode):
        result = bytearray()

        for arg in node.args:
            result.extend(self.visit_node(arg))
        result.extend(self.visit_node(node.callee))
        result.append(Opcodes.INVOKE)
        result.extend(Encoder.int16(len(node.args)))

        return result
    
    def visit_node_BinOpNode(self, node: BinOpNode):
        ops = {
            TokenType.Plus: Opcodes.ADD,
            TokenType.Multiply: Opcodes.MULTIPLY
        }
        return bytearray([*self.visit_node(node.left), *self.visit_node(node.right), ops[node.op]])

    def visit_node_DiscardNode(self, node: DiscardNode):
        return self.visit_node(node.value) + bytearray([Opcodes.DISCARD])
    
    def visit_node_ConstNode(self, node: ConstNode):
        ptr = self.module_stack[-1].push_const(node.value)

        return bytearray([Opcodes.PUSH_CONST, *Encoder.int32(ptr)])
    
    def visit_node_IdenNode(self, node: IdenNode):
        ptr = self.module_stack[-1].push_const(node.iden)
        return bytearray([Opcodes.GET, *Encoder.int32(ptr)])

    def dump(self):
        result = bytearray()
        result.extend(MAGIC)
        
        result.extend(Encoder.int32(len(self.module_cache.values())))
        for module in self.module_cache.values():
            result.extend(module.dump())

        return result