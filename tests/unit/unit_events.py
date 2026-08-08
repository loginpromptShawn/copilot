import threading
from unittest.mock import patch

from copilot_app.events.event_bus import EventBus
from copilot_app.events.event_types import UserCreatedEvent, SystemInfoUpdatedEvent, LogCleanupEvent
from copilot_app.events.subscribers import (
    handle_user_created,
    handle_system_info_updated,
    handle_log_cleanup,
)


def unit_subscribe_publish_unsubscribe():
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


def unit_thread_safety():
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


def unit_event_types_have_timestamps():
    evt = UserCreatedEvent(user_id=1, name="A")
    assert hasattr(evt, "timestamp")
    assert "Z" in evt.timestamp or "+00:00" in evt.timestamp

    evt2 = SystemInfoUpdatedEvent(os="macOS", version="14.0")
    assert hasattr(evt2, "timestamp")

    evt3 = LogCleanupEvent()
    assert hasattr(evt3, "timestamp")


def unit_handle_user_created_logs_and_calls_repo():
    with patch("copilot_app.events.subscribers.UserRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_user.return_value = None
        with patch("copilot_app.events.subscribers.logger") as mock_logger:
            handle_user_created(UserCreatedEvent(user_id=5, name="Bob"))
            mock_repo.get_user.assert_called_once_with(5)
            mock_logger.info.assert_called()
            mock_logger.exception.assert_not_called()


def unit_handle_user_created_handles_repo_exception():
    with patch("copilot_app.events.subscribers.UserRepository") as MockRepo:
        MockRepo.side_effect = RuntimeError("db down")
        with patch("copilot_app.events.subscribers.logger") as mock_logger:
            handle_user_created(UserCreatedEvent(user_id=1, name="A"))
            mock_logger.exception.assert_called_once()


def unit_handle_system_info_updated_saves_info():
    with patch("copilot_app.events.subscribers.SystemInfoRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.save_system_info.return_value = None
        with patch("copilot_app.events.subscribers.logger") as mock_logger:
            handle_system_info_updated(SystemInfoUpdatedEvent(os="linux", version="1.0"))
            mock_repo.save_system_info.assert_called_once_with("linux", "1.0")
            mock_logger.info.assert_called()
            mock_logger.exception.assert_not_called()


def unit_handle_system_info_updated_handles_exception():
    with patch("copilot_app.events.subscribers.SystemInfoRepository") as MockRepo:
        MockRepo.side_effect = RuntimeError("db down")
        with patch("copilot_app.events.subscribers.logger") as mock_logger:
            handle_system_info_updated(SystemInfoUpdatedEvent(os="win", version="2.0"))
            mock_logger.exception.assert_called_once()


def unit_handle_log_cleanup_logs():
    with patch("copilot_app.events.subscribers.logger") as mock_logger:
        handle_log_cleanup(LogCleanupEvent())
        mock_logger.info.assert_called_once()
