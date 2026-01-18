from .parser import Node, CallNode, ConstNode, IdenNode

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

class Instruction:
    def __init__(self):
        raise NotImplementedError(f"Cannot instantiate this instruction ({self.__class__.__name__})")
    def dump(self) -> bytes | bytearray:
        raise NotImplementedError(f"Cannot dump this instruction ({self.__class__.__name__})")

class SetConst(Instruction):
    def __init__(self, const: str | int | float):
        self.const = const

class GetGlobal(Instruction):
    def __init__(self, slot: int, name: str):
        self.slot = slot
        self.name = name

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
        self.locals = locals
        self.used_slots: set[int] = set()

        self.bytecode: bytearray | bytes | None = None 
    
    def reserve_slot(self):
        for i in range(self.args, self.args + self.locals):
            if i not in self.used_slots:
                self.used_slots.add(i)
                return i
            
        slot = self.locals + self.args
        self.locals += 1

        self.used_slots.add(slot)
        return slot
    
    def release_slot(self, slot: int):
        self.used_slots.remove(slot)

    def dump(self):
        assert self.bytecode is not None

        result = bytearray()
        result.extend(Encoder.int16(self.args))
        result.extend(Encoder.int16(self.locals))
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
        self.compile_method(self.module_stack[-1], "$global", [], module_ast)
        
        mod = self.module_stack.pop()

        assert mod.get_name() not in self.module_cache
        self.module_cache[mod.get_name()] = mod

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
    
    def dump(self):
        result = bytearray()

        for module in self.module_cache.values():
            result.extend(Encoder.str(module.get_name()))
            result.extend(module.dump())

        return result