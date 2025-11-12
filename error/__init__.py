class CodeError(Exception):
    def __init__(self, code: int = 1, *args):
        if code == 0:
            raise Exception(f"CodeError code cannot be OK")
        super().__init__(code, *args)
        self.code = code
        self.message = "; ".join([str(x) for x in args])

    def __str__(self) -> str:
        return f"{self.__class__.__name__} #{self.code}: {self.message or '*empty message*'}"