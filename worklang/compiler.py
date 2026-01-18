from .parser import Node, CallNode, ConstNode, IdenNode

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

class MethodContext:
    def __init__(self, module_name: str, method_name: str, method_args: list[str], locals: int = 0):
        self.module_name = module_name
        self.method_name = method_args
        self.method_args = method_args

        self.args = len(method_args)
        self.locals = locals
        self.used_slots: set[int] = set()
    
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

class Compiler:
    def __init__(self):
        self.method_context_stack: list[MethodContext] = []

    def compile_main_module(self, module_ast: list[Node]):
        self.compile_method("main", "$global", [], module_ast)

    def compile_method(self, module: str, method_name: str, method_args: list[str], method_ast: list[Node]):
        self.method_context_stack.append(MethodContext(module, method_name, method_args, len(method_args)))

        for i in method_ast:
            self.visit_node(i)

    def visit_node(self, node: Node) -> bytearray:
        return getattr(self, "visit_node_" + node.__class__.__name__, self.no_node_visitor)(node)
    def no_node_visitor(self, node: Node) -> bytearray:
        raise NotImplementedError(f"No visitor for node {node}")