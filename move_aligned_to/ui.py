from __future__ import annotations

import wx

from .controller import MoveAlignedController
from .model import Axis


class MoveAlignedFrame(wx.Frame):
    def __init__(self, controller: MoveAlignedController) -> None:
        super().__init__(
            None,
            title="Move Aligned To",
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        self.controller = controller

        panel = wx.Panel(self)
        outer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(
            panel, label=f"Captured {len(controller.moving_items)} item(s) to move."
        )
        heading.SetFont(heading.GetFont().Bold())
        outer.Add(heading, 0, wx.BOTTOM, 6)
        outer.Add(
            wx.StaticText(
                panel,
                label=(
                    "Now select the reference item(s) in the PCB editor,\n"
                    "then choose the alignment axis."
                ),
            ),
            0,
            wx.BOTTOM,
            12,
        )

        self.same_x = wx.RadioButton(
            panel,
            label="Same X — continue moving vertically",
            style=wx.RB_GROUP,
        )
        self.same_y = wx.RadioButton(
            panel, label="Same Y — continue moving horizontally"
        )
        outer.Add(self.same_x, 0, wx.BOTTOM, 4)
        outer.Add(self.same_y, 0, wx.BOTTOM, 12)

        self.reference_count = wx.StaticText(
            panel, label="Reference selection: not checked"
        )
        outer.Add(self.reference_count, 0, wx.BOTTOM, 10)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        check = wx.Button(panel, label="Check selection")
        align = wx.Button(panel, wx.ID_OK, label="Align and move")
        buttons.Add(check)
        buttons.AddStretchSpacer()
        buttons.Add(align)
        outer.Add(buttons, 0, wx.EXPAND | wx.BOTTOM, 12)

        hint = wx.StaticText(
            panel,
            label="Click in KiCad to place. Press Esc to cancel the entire operation.",
        )
        hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        outer.Add(hint)

        panel.SetSizer(outer)
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 16)
        self.SetSizerAndFit(frame_sizer)
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() | wx.STAY_ON_TOP)
        self.Centre()

        check.Bind(wx.EVT_BUTTON, self._on_refresh)
        align.Bind(wx.EVT_BUTTON, self._on_confirm)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        wx.CallAfter(self.refresh_count)

    def refresh_count(self) -> None:
        try:
            count = len(self.controller.reference_selection())
            self.reference_count.SetLabel(f"Reference selection: {count} item(s)")
        except Exception as exc:  # noqa: BLE001 - GUI boundary must keep the plugin alive
            self.reference_count.SetLabel(f"Could not read selection: {exc}")
        self.Layout()

    def _on_refresh(self, _event: wx.CommandEvent) -> None:
        self.refresh_count()

    def _on_confirm(self, _event: wx.CommandEvent) -> None:
        axis = Axis.SAME_X if self.same_x.GetValue() else Axis.SAME_Y
        try:
            self.controller.align(axis)
        except Exception as exc:  # noqa: BLE001 - surface API errors in the dialog
            wx.MessageBox(str(exc), "Move Aligned To", wx.OK | wx.ICON_ERROR, self)
            return
        self.Close()

    def _on_key(self, event: wx.KeyEvent) -> None:
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()


def run_window(controller: MoveAlignedController) -> None:
    app = wx.App(False)
    frame = MoveAlignedFrame(controller)
    frame.Show()
    app.MainLoop()
