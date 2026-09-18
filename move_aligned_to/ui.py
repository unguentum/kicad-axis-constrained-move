from __future__ import annotations

import wx

from .controller import MoveAlignedController
from .model import Axis


class MoveAlignedFrame(wx.Frame):
    """Small modeless companion window using KiCad's native wx toolkit."""

    POLL_INTERVAL_MS = 350

    def __init__(self, controller: MoveAlignedController) -> None:
        super().__init__(
            None,
            title="Move Aligned To — PCB Editor",
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        self.controller = controller
        self._reference_count = 0

        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)

        header = wx.BoxSizer(wx.HORIZONTAL)
        icon = wx.StaticBitmap(
            panel,
            bitmap=wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_OTHER, (32, 32)),
        )
        header.Add(icon, 0, wx.RIGHT | wx.TOP, 12)

        header_text = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(panel, label="Align one selection to another")
        title_font = title.GetFont()
        title_font.SetPointSize(title_font.GetPointSize() + 2)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        header_text.Add(title, 0, wx.BOTTOM, 3)
        subtitle = wx.StaticText(
            panel,
            label="Choose a shared centre axis, then place with native constrained Move.",
        )
        subtitle.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        header_text.Add(subtitle)
        header.Add(header_text, 1)
        root.Add(header, 0, wx.EXPAND | wx.BOTTOM, 16)

        selection_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Selections")
        selection_grid = wx.FlexGridSizer(cols=2, vgap=8, hgap=20)
        selection_grid.AddGrowableCol(1)
        selection_grid.Add(wx.StaticText(panel, label="Moving"), 0, wx.ALIGN_CENTER_VERTICAL)
        moving = wx.StaticText(
            panel, label=f"✓  {len(controller.moving_items)} item(s) captured"
        )
        moving.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        selection_grid.Add(moving, 0, wx.ALIGN_CENTER_VERTICAL)
        selection_grid.Add(wx.StaticText(panel, label="Reference"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.reference_status = wx.StaticText(panel, label="Select item(s) in the PCB Editor")
        selection_grid.Add(self.reference_status, 0, wx.ALIGN_CENTER_VERTICAL)
        selection_box.Add(selection_grid, 1, wx.EXPAND | wx.ALL, 10)
        root.Add(selection_box, 0, wx.EXPAND | wx.BOTTOM, 12)

        alignment_box = wx.StaticBoxSizer(wx.VERTICAL, panel, "Alignment and free movement")
        self.same_x = wx.RadioButton(
            panel,
            label="Same X centre     •     move vertically",
            style=wx.RB_GROUP,
        )
        self.same_y = wx.RadioButton(
            panel,
            label="Same Y centre     •     move horizontally",
        )
        alignment_box.Add(self.same_x, 0, wx.ALL, 9)
        alignment_box.Add(self.same_y, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 9)
        root.Add(alignment_box, 0, wx.EXPAND | wx.BOTTOM, 12)

        hint = wx.StaticText(
            panel,
            label="After starting Move: click to place · Esc cancels alignment and movement",
        )
        hint.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        root.Add(hint, 0, wx.BOTTOM, 16)

        buttons = wx.StdDialogButtonSizer()
        cancel = wx.Button(panel, wx.ID_CANCEL)
        self.align_button = wx.Button(panel, wx.ID_OK, "Align && Move")
        self.align_button.SetDefault()
        self.align_button.Disable()
        buttons.AddButton(cancel)
        buttons.AddButton(self.align_button)
        buttons.Realize()
        root.Add(buttons, 0, wx.EXPAND)

        panel.SetSizer(root)
        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        frame_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 18)
        self.SetSizerAndFit(frame_sizer)
        self.SetMinSize((530, -1))
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() | wx.STAY_ON_TOP)
        self.Centre()

        self.align_button.Bind(wx.EVT_BUTTON, self._on_confirm)
        cancel.Bind(wx.EVT_BUTTON, lambda _event: self.Close())
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key)
        self.Bind(wx.EVT_CLOSE, self._on_close)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_poll, self.timer)
        self.timer.Start(self.POLL_INTERVAL_MS)
        wx.CallAfter(self.refresh_reference_selection)

    def refresh_reference_selection(self) -> None:
        try:
            self._reference_count = len(self.controller.reference_selection())
            if self._reference_count:
                self.reference_status.SetLabel(f"✓  {self._reference_count} item(s) selected")
                self.reference_status.SetForegroundColour(
                    wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
                )
                self.align_button.Enable()
            else:
                self.reference_status.SetLabel("Select item(s) in the PCB Editor")
                self.reference_status.SetForegroundColour(
                    wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
                )
                self.align_button.Disable()
        except Exception as exc:  # noqa: BLE001 - GUI boundary must keep the plugin alive
            self._reference_count = 0
            self.reference_status.SetLabel(f"Could not read selection: {exc}")
            self.reference_status.SetForegroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)
            )
            self.align_button.Disable()
        self.Layout()

    def _on_poll(self, _event: wx.TimerEvent) -> None:
        self.refresh_reference_selection()

    def _on_confirm(self, _event: wx.CommandEvent) -> None:
        axis = Axis.SAME_X if self.same_x.GetValue() else Axis.SAME_Y
        self.timer.Stop()
        self.align_button.Disable()
        self.align_button.SetLabel("Starting Move…")
        try:
            self.controller.align(axis)
        except Exception as exc:  # noqa: BLE001 - surface API errors in the dialog
            wx.MessageBox(str(exc), "Move Aligned To", wx.OK | wx.ICON_ERROR, self)
            self.align_button.SetLabel("Align && Move")
            self.align_button.Enable(self._reference_count > 0)
            self.timer.Start(self.POLL_INTERVAL_MS)
            return
        self.Destroy()

    def _on_key(self, event: wx.KeyEvent) -> None:
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()

    def _on_close(self, event: wx.CloseEvent) -> None:
        self.timer.Stop()
        event.Skip()


def run_window(controller: MoveAlignedController) -> None:
    app = wx.App(False)
    frame = MoveAlignedFrame(controller)
    frame.Show()
    app.MainLoop()
