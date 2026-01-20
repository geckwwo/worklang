from .rtobjects import WLObject, Primitives, NIL
from .tempvm import VM
from typing import Callable

defaults = {}

def wrap(name: str | None = None):
    def inner(fn: Callable[[VM, list[WLObject]], WLObject]):
        nonlocal name

        if not name:
            name = fn.__name__
        
        defaults[f"{name}"] = WLObject(Primitives.Runnable, fn)
        
        return fn
    return inner

@wrap("Сообщить")
def tell(vm: VM, args: list[WLObject]):
    print(*args)
    return NIL