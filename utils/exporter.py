from __future__ import annotations
from pathlib import Path
import shutil


def export_project(root: str | Path = "/content/pokechamp-ai", target: str | Path = "/content/drive/MyDrive/pokechamp-ai-export"):
    root = Path(root)
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for item in root.iterdir():
        dst = target / item.name
        if item.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
    return target
