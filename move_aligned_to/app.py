from __future__ import annotations

import wx

from .adapter import KiCadAdapter
from .controller import MoveAlignedController
from .ui import run_window


def main() -> None:
    try:
        controller = MoveAlignedController(KiCadAdapter())
    except Exception as exc:
        app = wx.App(False)
        wx.MessageBox(str(exc), "Move Aligned To", wx.OK | wx.ICON_ERROR)
        app.Destroy()
        raise SystemExit(1) from exc

    run_window(controller)
