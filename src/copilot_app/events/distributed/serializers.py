from __future__ import annotations

import json
from typing import Any, Dict

from ..event_types import UserCreatedEvent, SystemInfoUpdatedEvent, LogCleanupEvent

_TYPE_MAP = {
    "UserCreatedEvent": UserCreatedEvent,
    "SystemInfoUpdatedEvent": SystemInfoUpdatedEvent,
    "LogCleanupEvent": LogCleanupEvent,
}


def serialize_event(event: Any) -> str:
    payload = {"_type": type(event).__name__}
    payload.update(event.__dict__)
    return json.dumps(payload)


def deserialize_event(json_str: str) -> Any:
    data: Dict = json.loads(json_str)
    tname = data.pop("_type", None)
    if not tname or tname not in _TYPE_MAP:
        raise ValueError("Unknown event type: %s" % (tname,))
    cls = _TYPE_MAP[tname]
    return cls(**data)
