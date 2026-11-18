
import os
import sys
from pathlib import Path

MAX_RETRIES = 3
DEBUG = True


def greet(name: str) -> str:
    return f"Hello, {name}!"


async def fetch_data(url: str) -> str:
    return url


class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def subtract(self, a: int, b: int) -> int:
        return a - b


def decorator(func):
    return func


@decorator
def decorated_function():
    return "Decorated!"


# End of file
LAST_VALUE = 42
