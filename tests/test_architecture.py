"""Structural tests: enforce AGENTS.md module map against on-disk reality.

Run as part of `make check` via pytest. If these tests fail, either:
- A file was moved/renamed without updating AGENTS.md, or
- A new top-level module was added without adding it to AGENTS.md.

Fix: update the Module Map section of AGENTS.md (or restore the moved file).
"""

from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "stock_adviser"

# All top-level modules explicitly listed in AGENTS.md module map.
# Update this set whenever you add/rename a root-level module in src/stock_adviser/.
DOCUMENTED_ROOT_MODULES = {
    "graph.py",
    "config.py",
    "llm.py",
    "models.py",
    "prompts.py",
    "state.py",
    "streaming.py",
    "__main__.py",
    "server.py",
}

# Documented sub-packages. Presence of the directory is sufficient —
# internal files may evolve without requiring AGENTS.md updates.
DOCUMENTED_SUBPACKAGES = {"tools", "api", "events"}

# Specific files within sub-packages that are explicitly named in AGENTS.md.
# Update when adding/renaming a file that AGENTS.md calls out by path.
DOCUMENTED_SUBPACKAGE_FILES = {
    "api/app.py",
    "api/session.py",
    "api/routes/health.py",
    "api/routes/chat.py",
    "api/routes/stream.py",
    "api/routes/settings.py",
    "events/types.py",
    "events/router.py",
}


class TestDocumentedPathsExist:
    """Every path declared in AGENTS.md must exist on disk."""

    def test_root_modules_exist(self):
        missing = [m for m in DOCUMENTED_ROOT_MODULES if not (SRC / m).exists()]
        assert not missing, (
            f"AGENTS.md module map references files that don't exist: {missing}\n"
            "Either restore the file or remove it from AGENTS.md."
        )

    def test_subpackages_exist(self):
        missing = [p for p in DOCUMENTED_SUBPACKAGES if not (SRC / p).is_dir()]
        assert not missing, f"AGENTS.md references sub-packages that don't exist as directories: {missing}"

    def test_named_subpackage_files_exist(self):
        missing = [f for f in DOCUMENTED_SUBPACKAGE_FILES if not (SRC / f).exists()]
        assert not missing, (
            f"AGENTS.md module map references sub-package files that don't exist: {missing}\n"
            "Either restore the file or remove it from AGENTS.md."
        )


class TestNoUndocumentedRootModules:
    """New top-level modules must be added to AGENTS.md before merging.

    Only the root of src/stock_adviser/ is checked — internal files within
    api/, events/, and tools/ are exempt.
    """

    def test_no_undocumented_root_modules(self):
        on_disk = {p.name for p in SRC.iterdir() if p.is_file() and p.suffix == ".py" and p.name != "__init__.py"}
        undocumented = on_disk - DOCUMENTED_ROOT_MODULES
        assert not undocumented, (
            f"New module(s) in src/stock_adviser/ not listed in AGENTS.md: {undocumented}\n"
            "Add an entry to the Module Map section of AGENTS.md, then add the path\n"
            "to DOCUMENTED_ROOT_MODULES in this file."
        )
