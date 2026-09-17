from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .model import Axis, aggregate_bounds, alignment_delta, stable_id

if TYPE_CHECKING:
    from .adapter import KiCadAdapter


class WorkflowError(RuntimeError):
    pass


class MoveAlignedController:
    def __init__(self, adapter: KiCadAdapter | Any) -> None:
        self.adapter = adapter
        self.moving_items = adapter.selection()
        if not self.moving_items:
            raise WorkflowError("Select at least one item to move before starting the plugin.")
        self.moving_ids = {stable_id(item) for item in self.moving_items}
        self.adapter.clear_selection()

    def reference_selection(self) -> Sequence:
        return self.adapter.selection()

    def align(self, axis: Axis) -> tuple[int, int, int]:
        references = list(self.reference_selection())
        if not references:
            raise WorkflowError("Select at least one reference item in the PCB editor.")

        overlap = self.moving_ids.intersection(stable_id(item) for item in references)
        if overlap:
            raise WorkflowError(
                "The moving and reference selections must be separate. "
                "Deselect the original moving items from the reference selection."
            )

        moving_bounds = aggregate_bounds(self.adapter.bounds_for(self.moving_items))
        reference_bounds = aggregate_bounds(self.adapter.bounds_for(references))
        dx, dy = alignment_delta(moving_bounds, reference_bounds, axis)
        self.adapter.align_and_move(self.moving_items, dx, dy, axis)
        return len(references), dx, dy
