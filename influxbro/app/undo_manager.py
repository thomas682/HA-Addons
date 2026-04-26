import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _looks_like_row(row: object) -> bool:
    if not isinstance(row, dict):
        return False
    return bool(row.get("_time")) and bool(row.get("_measurement")) and bool(row.get("_field"))


def _has_change_block_ref(meta: object) -> bool:
    if not isinstance(meta, dict):
        return False
    bid = str(meta.get("change_block_id") or "").strip()
    return bool(bid)


@dataclass
class UndoStatus:
    ok: bool
    compatible: bool
    locked: bool
    locked_reason: str
    undo_count: int
    repeat_count: int
    undo_available: bool
    repeat_available: bool
    last_undo_action: dict[str, Any] | None
    last_repeat_action: dict[str, Any] | None


class UndoManager:
    """Server-side linear undo/repeat history for write actions.

    Storage is a single JSON file with two stacks:
    - undo: actions that can be undone
    - redo: actions that can be repeated (redo)
    """

    def __init__(self, base_dir: Path, max_entries: int = 100):
        self._lock = threading.RLock()
        self._base_dir = Path(base_dir)
        self._path = self._base_dir / "undo_history.json"
        self._max_entries = int(max(1, min(1000, max_entries)))
        self._loaded = False
        self._compatible = True
        self._locked_reason = ""
        self._undo: list[dict[str, Any]] = []
        self._redo: list[dict[str, Any]] = []

    def set_max_entries(self, max_entries: int) -> None:
        with self._lock:
            self._max_entries = int(max(1, min(1000, int(max_entries))))
            if len(self._undo) > self._max_entries:
                self._undo = self._undo[-self._max_entries :]
            self._persist()

    def _ensure_loaded(self) -> None:
        with self._lock:
            if self._loaded:
                return
            self._loaded = True
            try:
                if not self._path.exists():
                    return
                raw = self._path.read_text(encoding="utf-8", errors="replace")
                j = json.loads(raw) if raw.strip() else {}
                if not isinstance(j, dict):
                    raise ValueError("invalid undo history root")
                if int(j.get("v") or 0) != 1:
                    raise ValueError("unsupported undo history version")
                undo = j.get("undo")
                redo = j.get("redo")
                if not isinstance(undo, list) or not isinstance(redo, list):
                    raise ValueError("invalid stacks")
                # Basic schema validation; lock if incompatible.
                for it in (undo + redo):
                    if not isinstance(it, dict):
                        raise ValueError("invalid entry")
                    if not it.get("action_id") or not it.get("group_id") or not it.get("created_at"):
                        raise ValueError("missing required fields")
                    before_rows = it.get("before_rows")
                    after_rows = it.get("after_rows")
                    if not isinstance(before_rows, list) or not isinstance(after_rows, list):
                        raise ValueError("before_rows/after_rows must be lists")
                    meta = it.get("meta")
                    if before_rows or after_rows:
                        if any(not _looks_like_row(r) for r in before_rows + after_rows):
                            raise ValueError("invalid row shape")
                    else:
                        # Allow ref-only entries that point at a persisted ChangeBlock.
                        if not _has_change_block_ref(meta):
                            raise ValueError("empty action without change_block_id")
                self._undo = undo
                self._redo = redo
            except Exception as e:
                self._compatible = False
                self._locked_reason = f"Inkompatible Undo-History: {e}"
                self._undo = []
                self._redo = []

    def _persist(self) -> None:
        with self._lock:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            payload = {
                "v": 1,
                "updated_at": _utc_now_iso_ms(),
                "max_entries": self._max_entries,
                "undo": self._undo,
                "redo": self._redo,
            }
            tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
            tmp.replace(self._path)

    def status(self) -> UndoStatus:
        self._ensure_loaded()
        with self._lock:
            locked = not self._compatible
            undo_count = len(self._undo)
            redo_count = len(self._redo)

            def _undo_supported(a: dict[str, Any] | None) -> bool:
                if not a or not isinstance(a, dict):
                    return False
                meta = a.get("meta") if isinstance(a.get("meta"), dict) else {}
                # default True
                if meta.get("undo_supported") is False:
                    return False
                return True

            return UndoStatus(
                ok=True,
                compatible=bool(self._compatible),
                locked=bool(locked),
                locked_reason=str(self._locked_reason or ""),
                undo_count=undo_count,
                repeat_count=redo_count,
                undo_available=bool(undo_count > 0 and not locked and _undo_supported(self._undo[-1] if self._undo else None)),
                repeat_available=bool(redo_count > 0 and not locked),
                last_undo_action=self._undo[-1] if self._undo else None,
                last_repeat_action=self._redo[-1] if self._redo else None,
            )

    def clear(self) -> None:
        with self._lock:
            self._compatible = True
            self._locked_reason = ""
            self._undo = []
            self._redo = []
            self._loaded = True
            try:
                if self._path.exists():
                    self._path.unlink()
            except Exception:
                # If unlink fails, keep an empty file.
                self._persist()

    def register_action(
        self,
        action_type: str,
        bucket: str,
        measurement: str,
        group_label: str,
        before_rows: list[dict[str, Any]],
        after_rows: list[dict[str, Any]],
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a completed user action.

        Clears redo stack (classic behavior).
        """

        self._ensure_loaded()
        with self._lock:
            if not self._compatible:
                raise RuntimeError(self._locked_reason or "Undo history incompatible")

            before_rows = [r for r in (before_rows or []) if _looks_like_row(r)]
            after_rows = [r for r in (after_rows or []) if _looks_like_row(r)]
            meta = meta or {}
            if not before_rows and not after_rows and not _has_change_block_ref(meta):
                raise ValueError("empty action")

            action = {
                "action_id": str(uuid.uuid4()),
                "group_id": str(uuid.uuid4()),
                "created_at": _utc_now_iso_ms(),
                "action_type": str(action_type or "update"),
                "bucket": str(bucket or ""),
                "measurement": str(measurement or ""),
                "status": "done",
                "undone": False,
                "repeat_available": False,
                "label": str(group_label or ""),
                "before_rows": before_rows,
                "after_rows": after_rows,
                "meta": meta,
            }

            self._undo.append(action)
            self._redo = []
            # Trim oldest
            if len(self._undo) > self._max_entries:
                self._undo = self._undo[-self._max_entries :]
            self._persist()
            return action

    def pop_undo(self) -> dict[str, Any] | None:
        self._ensure_loaded()
        with self._lock:
            if not self._compatible:
                raise RuntimeError(self._locked_reason or "Undo history incompatible")
            if not self._undo:
                return None
            return self._undo.pop()

    def push_redo(self, action: dict[str, Any]) -> None:
        self._ensure_loaded()
        with self._lock:
            if not isinstance(action, dict):
                return
            self._redo.append(action)
            self._persist()

    def pop_redo(self) -> dict[str, Any] | None:
        self._ensure_loaded()
        with self._lock:
            if not self._compatible:
                raise RuntimeError(self._locked_reason or "Undo history incompatible")
            if not self._redo:
                return None
            return self._redo.pop()

    def push_undo(self, action: dict[str, Any]) -> None:
        self._ensure_loaded()
        with self._lock:
            if not isinstance(action, dict):
                return
            self._undo.append(action)
            if len(self._undo) > self._max_entries:
                self._undo = self._undo[-self._max_entries :]
            self._persist()

    def history(self, limit: int = 200) -> list[dict[str, Any]]:
        self._ensure_loaded()
        with self._lock:
            lim = int(max(1, min(2000, limit)))
            # newest first
            return list(reversed(self._undo))[:lim]
