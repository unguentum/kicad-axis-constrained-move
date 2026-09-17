from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .controller import MoveAlignedController
from .model import Axis


class MoveAlignedWindow:
    def __init__(self, root: tk.Tk, controller: MoveAlignedController) -> None:
        self.root = root
        self.controller = controller
        self.axis = tk.StringVar(value=Axis.SAME_X.value)
        self.reference_count = tk.StringVar(value="Reference selection: not checked")

        root.title("Move Aligned To")
        root.resizable(False, False)
        root.attributes("-topmost", True)
        root.protocol("WM_DELETE_WINDOW", root.destroy)

        frame = ttk.Frame(root, padding=16)
        frame.grid(sticky="nsew")

        ttk.Label(
            frame,
            text=f"Captured {len(controller.moving_items)} item(s) to move.",
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            frame,
            text="Now select the reference item(s) in the PCB editor,\nthen choose the alignment axis.",
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 12))

        ttk.Radiobutton(
            frame,
            text="Same X  — continue moving vertically",
            variable=self.axis,
            value=Axis.SAME_X.value,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Radiobutton(
            frame,
            text="Same Y  — continue moving horizontally",
            variable=self.axis,
            value=Axis.SAME_Y.value,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=2)

        ttk.Label(frame, textvariable=self.reference_count).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(12, 10)
        )
        ttk.Button(frame, text="Check selection", command=self.refresh_count).grid(
            row=5, column=0, sticky="w"
        )
        ttk.Button(frame, text="Align and move", command=self.confirm).grid(
            row=5, column=1, sticky="e", padx=(24, 0)
        )

        ttk.Label(
            frame,
            text="Click in KiCad to place. Press Esc to cancel the entire operation.",
            foreground="#555555",
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))

        root.bind("<Return>", lambda _event: self.confirm())
        root.bind("<Escape>", lambda _event: root.destroy())
        root.after(100, self.refresh_count)

    def refresh_count(self) -> None:
        try:
            count = len(self.controller.reference_selection())
            self.reference_count.set(f"Reference selection: {count} item(s)")
        except Exception as exc:  # noqa: BLE001 - GUI boundary must keep the plugin alive
            self.reference_count.set(f"Could not read selection: {exc}")

    def confirm(self) -> None:
        try:
            axis = Axis(self.axis.get())
            self.controller.align(axis)
        except Exception as exc:  # noqa: BLE001 - surface API errors in the dialog
            messagebox.showerror("Move Aligned To", str(exc), parent=self.root)
            return

        self.root.destroy()


def run_window(controller: MoveAlignedController) -> None:
    root = tk.Tk()
    MoveAlignedWindow(root, controller)
    root.mainloop()
