from .parser import Node, CallNode, ConstNode, IdenNode, ModuleDeclNode
import struct

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
    def float(cls, f: float):
        return struct.pack("f", f)

class ConstEntry:
    INT = 1
    FLOAT = 2
    STRING = 3

class Opcodes:
    PUSH_CONST = 0x01

    GET_GLOBAL = 0x0A

    INVOKE = 0x10

    RETURN_NOTHING = 0x7F

CONST_TYPE = int | float | str

class Module:
    def __init__(self):
        self.name: str | None = None
        self.methods: dict[str, Method] = {}

    def set_name(self, name: str):
        self.name = name
    def get_name(self):
        if self.name is None:
            raise ValueError("Modules should have a name!")
        return self.name
    
    def dump(self):
        result = bytearray()

        result.extend(Encoder.str(self.get_name()))
        result.extend(Encoder.int16(len(self.methods)))
        for name, method in self.methods.items():
            result.extend(Encoder.str(name))
            result.extend(method.dump())

        return result

class Method:
    def __init__(self, module: Module, method_name: str, method_args: list[str], locals: int = 0):
        self.module = module
        self.method_name = method_name
        self.method_args = method_args

        self.args = len(method_args)

        self.bytecode: bytearray | bytes | None = None 
        self.const_pool: list[CONST_TYPE] = []

    def get_signature(self):
        return f"{self.method_name}/{len(self.method_args)}"

    def push_const(self, const: CONST_TYPE):
        if const in self.const_pool:
            return self.const_pool.index(const)
        self.const_pool.append(const)
        return len(self.const_pool) - 1

    def dump(self):
        assert self.bytecode is not None

        result = bytearray()
        result.extend(Encoder.int16(self.args))
        
        result.extend(Encoder.int32(len(self.const_pool)))
        for entry in self.const_pool:
            if isinstance(entry, str):
                result.append(ConstEntry.STRING)
                result.extend(Encoder.str(entry))
            else:
                raise NotImplementedError(f"Cannot serialize const pool entry {entry}")

        result.extend(Encoder.int32(len(self.bytecode)))
        result.extend(self.bytecode)
        return result

class Compiler:
    def __init__(self):
        self.method_stack: list[Method] = []
        self.module_stack: list[Module] = []

        self.module_cache: dict[str, Module] = {}

    def compile_module(self, module_ast: list[Node]):
        self.module_stack.append(Module())
        method = self.compile_method(self.module_stack[-1], "$global", [], module_ast)
        mod = self.module_stack.pop()

        assert mod.get_name() not in self.module_cache
        self.module_cache[mod.get_name()] = mod

        mod.methods[method.get_signature()] = method

        return mod

    def compile_method(self, module: Module, method_name: str, method_args: list[str], method_ast: list[Node]):
        self.method_stack.append(Method(module, method_name, method_args, len(method_args)))
        method_bytecode = bytearray()

        for i in method_ast:
            method_bytecode.extend(self.visit_node(i))
        
        ctx = self.method_stack.pop()
        ctx.bytecode = method_bytecode
        return ctx

    def visit_node(self, node: Node) -> bytearray:
        return getattr(self, "visit_node_" + node.__class__.__name__, self.no_node_visitor)(node)
    def no_node_visitor(self, node: Node) -> bytearray:
        raise NotImplementedError(f"No visitor for node {node}")
    
    def visit_node_ModuleDeclNode(self, node: ModuleDeclNode):
        self.module_stack[-1].set_name(".".join(node.modname))
        return bytearray()

    def visit_node_CallNode(self, node: CallNode):
        result = bytearray()

        for arg in node.args:
            result.extend(self.visit_node(arg))
        
        result.extend(Encoder.int16(len(node.args)))
        result.extend(self.visit_node(node.callee))
        result.append(Opcodes.INVOKE)

        return result
    
    def visit_node_ConstNode(self, node: ConstNode):
        ptr = self.method_stack[-1].push_const(node.value)

        return bytearray([Opcodes.PUSH_CONST, *Encoder.int32(ptr)])
    
    def visit_node_IdenNode(self, node: IdenNode):
        ptr = self.method_stack[-1].push_const(node.iden)
        return bytearray([Opcodes.GET_GLOBAL, *Encoder.int32(ptr)])

    def dump(self):
        result = bytearray()

        for module in self.module_cache.values():
            result.extend(Encoder.str(module.get_name()))
            result.extend(module.dump())

        return result