from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from .adapter import KiCadAdapter
from .controller import MoveAlignedController
from .ui import run_window


def main() -> None:
    try:
        controller = MoveAlignedController(KiCadAdapter())
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Move Aligned To", str(exc), parent=root)
        root.destroy()
        raise SystemExit(1) from exc

    run_window(controller)
