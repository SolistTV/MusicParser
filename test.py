class A:
    def __init__(self):
        print("init")
        self.name = "test"

    def __new__(cls, *args, **kwargs):
        print("new")


a = A()
