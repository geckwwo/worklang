import enum
import importlib
from typing import cast
from .compiler import ConstEntry, Opcodes, MAGIC
from .rtobjects import *

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

class ExecutorStepResult(enum.Enum):
    CONTINUE = 1
    END = 2
    ASYNC_YIELD = 3

class ModuleContext:
    def __init__(self, module: WLModule):
        self.module = module
        self.globals: dict[str, WLObject] = {} | cast(dict[str, WLObject], importlib.import_module("worklang.stdlib").defaults)

class BinOperation(enum.Enum):
    ADD = 1
    MULTIPLY = 2

def operate_bi(left: WLObject, right: WLObject, op: BinOperation):
    match left.object_type:
        case Primitives.Number:
            assert right.object_type == left.object_type, "Only numbers can be operated together"
            v = 0
            match op:
                case BinOperation.ADD:
                    v = left.value + right.value
                case BinOperation.MULTIPLY:
                    v = left.value * right.value
                case _:
                    raise NotImplementedError(f"unknown op {op}")
            return WLObject(Primitives.Number, v)
        case _:
            raise NotImplementedError(f"cannot operate on {left.object_type}")

class MethodContext:
    def __init__(self, method: WLMethod):
        self.method = method
        self.locals: list[WLObject] = [NIL] * (method.argcount)
        self.stack: list[WLObject] = []
        self.bs = ByteStream(method.bytecode)

    def step(self, executor: 'Executor', vm: 'VM') -> tuple[ExecutorStepResult, WLObject | None]:
        if self.bs.over():
            return ExecutorStepResult.END, NIL
        opcode = self.bs.byte()
        
        if opcode == Opcodes.NOP:
            pass
        elif opcode == Opcodes.PUSH_CONST:
            ptr = self.bs.int32()
            raw_obj = self.method.constpool[ptr]
            if isinstance(raw_obj, str):
                self.stack.append(WLObject(Primitives.String, raw_obj))
            elif isinstance(raw_obj, int):
                self.stack.append(WLObject(Primitives.Number, raw_obj))
            else:
                raise NotImplementedError(f"Unknown raw object type {raw_obj}")
        elif opcode == Opcodes.GET_GLOBAL:
            ptr = self.bs.int32()
            iden = self.method.constpool[ptr]

            assert isinstance(iden, str)
            self.stack.append(executor.mod_ctx.globals[iden])
        elif opcode == Opcodes.INVOKE:
            argcount = self.bs.int16()
            callee = self.stack.pop()

            args: list[WLObject] = []
            for _ in range(argcount):
                args.insert(0, self.stack.pop())
            
            assert callee.object_type == Primitives.Runnable
            self.stack.append(callee.value(vm, args)) # type: ignore
        elif opcode == Opcodes.DISCARD:
            self.stack.pop()
        elif opcode == Opcodes.MULTIPLY:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(operate_bi(left, right, BinOperation.MULTIPLY))
        elif opcode == Opcodes.ADD:
            right = self.stack.pop()
            left = self.stack.pop()
            self.stack.append(operate_bi(left, right, BinOperation.ADD))
        else:
            raise NotImplementedError(f"Unknown opcode {hex(opcode)}")
        return ExecutorStepResult.CONTINUE, None

class Executor:
    def __init__(self, mod_ctx: ModuleContext, method_ctx: MethodContext):
        self.mod_ctx = mod_ctx
        self.method_ctx = method_ctx

    def step(self, vm: 'VM'):
        return self.method_ctx.step(self, vm)

class ByteStream:
    def __init__(self, arr: bytearray | bytes):
        self.arr = arr
        self.idx = 0
    def byte(self):
        val = self.arr[self.idx]
        self.idx += 1
        return val
    def int16(self):
        val = int.from_bytes(self.arr[self.idx:self.idx+2], "big")
        self.idx += 2
        return val
    def int32(self):
        val = int.from_bytes(self.arr[self.idx:self.idx+4], "big")
        self.idx += 4
        return val
    def str(self):
        length = self.int32()
        val = self.arr[self.idx:self.idx+length].decode("utf-8")
        self.idx += length
        return val
    def bytes(self, amt: int):
        val = self.arr[self.idx:self.idx+amt]
        self.idx += amt
        return val
    def varint(self):
        amt = self.byte()
        return int.from_bytes(self.bytes(amt), "big", signed=True)
    def over(self):
        return self.idx >= len(self.arr)

class VM:
    def __init__(self):
        self.modules: dict[str, WLModule] = {}
        self.executor_stack: list[Executor] = []

    def load_from_bytes(self, thing: bytearray | bytes):
        s = ByteStream(thing)

        magic = s.bytes(8)
        assert magic == MAGIC, "Wrong magic"

        module_count = s.int32()
        for _ in range(module_count):
            module_name = s.str()
            method_count = s.int16()

            methods: dict[str, WLMethod] = {}
            module = WLModule(module_name, methods)

            for _ in range(method_count):
                method_signature = s.str()
                arg_count = s.int16()

                const_count = s.int32()
                const_pool: list[int | float | str] = []
                for _ in range(const_count):
                    typ = s.byte()
                    if typ == ConstEntry.STRING:
                        const_pool.append(s.str())
                    elif typ == ConstEntry.INT:
                        const_pool.append(s.varint())
                    else:
                        raise NotImplementedError(f"Unknown const pool entry {typ}")
                
                bytecode_length = s.int32()
                bytecode = s.bytes(bytecode_length)
                methods[method_signature] = WLMethod(module, arg_count, const_pool, bytecode)
            self.modules[module_name] = module

    def run(self, module: str, method_signature: str):
        mod_ctx = ModuleContext(self.modules[module])
        method_ctx = MethodContext(mod_ctx.module.methods[method_signature])
        executor = Executor(mod_ctx, method_ctx)

        self.executor_stack.append(executor)
        while True:
            ex = self.executor_stack[-1]
            res, val = ex.step(self)
            if res == ExecutorStepResult.CONTINUE:
                pass
            elif res == ExecutorStepResult.END:
                self.executor_stack.pop()
                if len(self.executor_stack) == 0:
                    break
                self.executor_stack[-1].method_ctx.stack.append(cast(WLObject, val))
            else:
                raise NotImplementedError(f"Step {res}")
