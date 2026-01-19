import enum
from typing import Any

ConstType = int | str | float

class WLMethod:
    def __init__(self, module: 'WLModule', argcount: int, constpool: list[ConstType], bytecode: bytearray | bytes):
        self.argcount = argcount
        self.constpool = constpool
        self.bytecode = bytecode

class WLModule:
    def __init__(self, name: str, methods: dict[str, WLMethod]):
        self.name = name
        self.methods = methods

class Primitives(enum.Enum):
    Number = 1
    String = 2
    Bool = 3
    Nil = -67

class WLObject:
    def __init__(self, object_type: Primitives, value: Any = None):
        self.object_type = object_type
        self.value = value
    def __eq__(self, other: WLObject | Any):
        if not isinstance(other, WLObject):
            return False
        if self.object_type != other.object_type:
            return False
        return self.value == other.value

class ModuleContext:
    def __init__(self, module: WLModule):
        self.module = module
        self.globals: dict[str, WLObject] = {}
class MethodContext:
    def __init__(self, method: WLMethod):
        self.locals: list[WLObject] = [WLObject(Primitives.Nil)] * (method.argcount)
        self.ip = -1

class Executor:
    pass

class VM:
    def __init__(self):
        self.modules: dict[str, WLModule] = {}

    def load_from_bytes(self, thing: bytearray | bytes):
        pass

    def run(self, module: str, method_signature: str):
        pass