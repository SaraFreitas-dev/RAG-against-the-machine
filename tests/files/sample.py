
"""Sample Python file for testing AST-based chunking."""

import os
import sys
from pathlib import Path
from typing import Callable


MAX_RETRIES = 3
DEBUG = True


def get_environment_info() -> dict[str, str]:
    """Return basic information about the current environment."""
    return {
        "working_directory": os.getcwd(),
        "python_version": sys.version,
        "home_directory": str(Path.home()),
    }


def greet(name: str) -> str:
    """Return a personalized greeting."""
    return f"Hello, {name}!"


async def fetch_data(url: str) -> str:
    """Simulate fetching data from a URL."""
    return url


class Calculator:
    """Perform basic arithmetic operations."""

    def add(self, a: int, b: int) -> int:
        """Return the sum of two integers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Return the difference between two integers."""
        return a - b


def decorator(func: Callable[[], str]) -> Callable[[], str]:
    """Return the original function without modifying it."""
    return func


@decorator
def decorated_function() -> str:
    """Return a message from a decorated function."""
    return "Decorated!"


# End of file
LAST_VALUE = 42
