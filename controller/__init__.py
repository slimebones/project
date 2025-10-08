import sys


def response(*messages, end: str = "\n", sep: str = " "):
    print(*messages, file=sys.stderr, end=end, sep=sep)