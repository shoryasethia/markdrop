import sys


def test_import_does_not_inject_mocks():
    for name in ("torch", "transformers", "docling", "docling_core"):
        module = sys.modules.get(name)
        if module is not None:
            assert not type(module).__name__ == "MagicMock", (
                f"{name} was replaced with MagicMock at import time"
            )


def test_package_version():
    import markdrop

    assert markdrop.__version__
    assert isinstance(markdrop.__version__, str)
