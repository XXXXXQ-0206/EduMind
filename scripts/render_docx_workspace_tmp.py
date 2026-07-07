from __future__ import annotations

import runpy
import sys
import tempfile
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / ".codex_tmp" / "lo_tmp"
RENDER_SCRIPT = Path(
    r"C:\Users\秋刀鱼\.codex\plugins\cache\openai-primary-runtime\documents\26.630.12135\skills\documents\render_docx.py"
)


class WorkspaceTemporaryDirectory:
    def __init__(self, suffix: str | None = None, prefix: str | None = None, dir: str | None = None, **_: object) -> None:
        base = Path(dir) if dir else TMP_ROOT
        base.mkdir(parents=True, exist_ok=True)
        self.name = str(base / f"{prefix or 'tmp_'}{uuid.uuid4().hex}{suffix or ''}")
        Path(self.name).mkdir(parents=True, exist_ok=False)

    def __enter__(self) -> str:
        return self.name

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def cleanup(self) -> None:
        return None


def main() -> None:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(TMP_ROOT)
    tempfile.TemporaryDirectory = WorkspaceTemporaryDirectory  # type: ignore[assignment]
    runpy.run_path(str(RENDER_SCRIPT), run_name="__main__")


if __name__ == "__main__":
    main()
