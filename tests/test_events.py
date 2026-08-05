import threading

from copilot_app.events.event_bus import EventBus
from copilot_app.events.event_types import UserCreatedEvent


def test_subscribe_publish_unsubscribe():
    bus = EventBus()
    calls = []

    def handler(evt):
        calls.append(evt)

    bus.subscribe(UserCreatedEvent, handler)
    evt = UserCreatedEvent(user_id=1, name="A")
    bus.publish(evt)
    assert len(calls) == 1
    bus.unsubscribe(UserCreatedEvent, handler)
    bus.publish(UserCreatedEvent(user_id=2, name="B"))
    assert len(calls) == 1


def test_thread_safety():
    bus = EventBus()
    counter = {"n": 0}
    lock = threading.Lock()

    def handler(evt):
        with lock:
            counter["n"] += 1

    bus.subscribe(UserCreatedEvent, handler)

    def pub_loop():
        for i in range(100):
            bus.publish(UserCreatedEvent(user_id=i, name=str(i)))

    threads = [threading.Thread(target=pub_loop) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert counter["n"] == 500
