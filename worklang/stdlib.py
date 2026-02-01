from .rtobjects import WLObject, Primitives, NIL
from .tempvm import Executor
from typing import Callable

defaults = {}

def wrap(name: str | None = None):
    def inner(fn: Callable[[Executor, list[WLObject]], WLObject]):
        nonlocal name

        if not name:
            name = fn.__name__
        
        defaults[f"{name}"] = WLObject(Primitives.Runnable, fn)
        
        return fn
    return inner

@wrap("Сообщить")
def tell(ex: Executor, args: list[WLObject]):
    print(*args)
    return NIL

@wrap("__СисВызов_ИмпортМодуля")
def modimport(ex: Executor, args: list[WLObject]):
    assert args[0].object_type == Primitives.String
    return WLObject(Primitives.Module, ex.vm.load_module(args[0].value))