class WLModule:
    pass

class VM:
    def __init__(self):
        self.modules: dict[str, WLModule] = {}

    def load_from_bytes(self, thing: bytearray | bytes):
        pass

    def run(self, module: str, method_signature: str):
        pass