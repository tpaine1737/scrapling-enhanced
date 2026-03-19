import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.python import Function


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require a Camoufox browser",
    )


def pytest_collection_modifyitems(config: Config, items: list[pytest.Item]) -> None:
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="needs --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)
