from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from google.protobuf.empty_pb2 import Empty
from kipy import KiCad
from kipy.board_types import BoardItem, Group
from kipy.geometry import Vector2
from kipy.proto.board import board_commands_pb2

from .model import Axis, Bounds, stable_id


class UnsupportedItemError(RuntimeError):
    pass


class KiCadAdapter:
    def __init__(self) -> None:
        self.kicad = KiCad()
        self.board = self.kicad.get_board()

    def selection(self) -> list[BoardItem]:
        return list(self.board.get_selection())

    def clear_selection(self) -> None:
        self.board.clear_selection()

    def bounds_for(self, items: Sequence[BoardItem]) -> list[Bounds]:
        boxes = self.board.get_item_bounding_box(items, include_text=False)
        result: list[Bounds] = []

        for item, box in zip(items, boxes):
            if box is None:
                raise UnsupportedItemError(
                    f"{type(item).__name__} {stable_id(item)} has no geometric bounding box"
                )
            result.append(
                Bounds(
                    box.pos.x,
                    box.pos.y,
                    box.pos.x + box.size.x,
                    box.pos.y + box.size.y,
                )
            )
        return result

    def _expand_groups(self, items: Iterable[BoardItem]) -> list[BoardItem]:
        expanded: list[BoardItem] = []
        seen: set[str] = set()

        def visit(item: BoardItem) -> None:
            key = stable_id(item)
            if key in seen:
                return
            seen.add(key)
            if isinstance(item, Group):
                for child in item.items:
                    visit(child)
            else:
                expanded.append(item)

        for selected in items:
            visit(selected)
        return expanded

    @staticmethod
    def _translate_item(item: BoardItem, delta: Vector2) -> None:
        descriptor = getattr(type(item), "position", None)
        if descriptor is not None and getattr(descriptor, "fset", None) is not None:
            item.position = item.position + delta
            return

        mover = getattr(item, "move", None)
        if callable(mover):
            try:
                mover(delta)
                return
            except NotImplementedError:
                pass

        if hasattr(item, "start") and hasattr(item, "end"):
            item.start = item.start + delta
            if hasattr(item, "mid"):
                item.mid = item.mid + delta
            item.end = item.end + delta
            return

        raise UnsupportedItemError(
            f"{type(item).__name__} {stable_id(item)} cannot be translated by the KiCad 10 API"
        )

    def align_and_move(
        self,
        moving_items: Sequence[BoardItem],
        dx: int,
        dy: int,
        axis: Axis,
    ) -> None:
        delta = Vector2.from_xy(dx, dy)
        concrete = self._expand_groups(moving_items)

        # Validate every item before opening a commit or modifying anything.
        for item in concrete:
            if not self._is_translatable(item):
                raise UnsupportedItemError(
                    f"{type(item).__name__} {stable_id(item)} cannot be translated by the KiCad 10 API"
                )

        commit = self.board.begin_commit()
        try:
            for item in concrete:
                self._translate_item(item, delta)
            updated = self.board.update_items(concrete)
            if len(updated) != len(concrete):
                raise RuntimeError("KiCad did not update every selected item")

            # InteractiveMoveItems adopts the open commit. Clicking commits both the
            # alignment and final move; Escape rolls both back as one operation.
            self._interactive_move_on_axis(
                [item.id for item in moving_items],
                Axis.SAME_Y if axis is Axis.SAME_X else Axis.SAME_X,
            )
        except Exception:
            self.board.drop_commit(commit)
            raise

    def _interactive_move_on_axis(self, item_ids: Sequence[Any], movement_axis: Axis) -> None:
        """Send KiCad's backwards-compatible axis field before kicad-python exposes it.

        Field 3 is ``AxisAlignment`` in our KiCad API patch. Protobuf preserves this unknown
        field when used with an older generated Python class, so the bridge can disappear once
        the matching kicad-python release grows an ``axis_constraint`` argument.
        """
        command = board_commands_pb2.InteractiveMoveItems()
        command.board.CopyFrom(self.board.document)
        command.items.extend(item_ids)
        wire_value = 1 if movement_axis is Axis.SAME_X else 2
        command.MergeFromString(bytes((0x18, wire_value)))
        self.board.client.send(command, Empty)

    @staticmethod
    def _is_translatable(item: BoardItem) -> bool:
        descriptor = getattr(type(item), "position", None)
        if descriptor is not None and getattr(descriptor, "fset", None) is not None:
            return True
        if callable(getattr(item, "move", None)):
            # BoardShape.move exists as an abstract fallback, so this is only a
            # preliminary check; _translate_item remains the source of truth.
            try:
                return type(item).move is not getattr(Any, "move", None)
            except AttributeError:
                return True
        return hasattr(item, "start") and hasattr(item, "end")
