import json

from copilot_app.events.distributed.transport import InMemoryTransport
from copilot_app.events.distributed.serializers import serialize_event, deserialize_event
from copilot_app.events.distributed.distributed_event_bus import DistributedEventBus
from copilot_app.events.event_types import UserCreatedEvent


def test_serialize_deserialize():
    evt = UserCreatedEvent(user_id=1, name="A")
    js = serialize_event(evt)
    obj = deserialize_event(js)
    assert isinstance(obj, UserCreatedEvent)
    assert obj.user_id == 1


def test_inmemory_transport_publish_subscribe():
    transport = InMemoryTransport()
    received = []

    def handler(msg):
        received.append(msg)

    transport.subscribe("t1", handler)
    transport.publish("t1", "hello")
    assert received == ["hello"]


def test_distributed_bus_roundtrip():
    transport = InMemoryTransport()
    bus = DistributedEventBus(transport=transport)
    received = []

    def handle(evt):
        received.append(evt)

    bus.subscribe(UserCreatedEvent, handle)
    evt = UserCreatedEvent(user_id=42, name="bob")
    bus.publish(evt)
    # in-memory transport and local bus should trigger handler
    assert any(isinstance(x, UserCreatedEvent) and x.user_id == 42 for x in received)
