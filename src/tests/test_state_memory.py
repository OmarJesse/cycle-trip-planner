import time

from src.state.memory import InMemoryConversationStore


def test_get_or_create_returns_same_state_for_same_id():
    store = InMemoryConversationStore.create(max_age_seconds=3600, max_count=100)
    a = store.get_or_create("abc")
    b = store.get_or_create("abc")
    assert a.conversation_id == "abc"
    assert b.conversation_id == "abc"


def test_get_or_create_assigns_a_new_id_when_none_provided():
    store = InMemoryConversationStore.create(max_age_seconds=3600, max_count=100)
    a = store.get_or_create(None)
    b = store.get_or_create(None)
    assert a.conversation_id and b.conversation_id
    assert a.conversation_id != b.conversation_id


def test_save_and_retrieve_roundtrip():
    store = InMemoryConversationStore.create(max_age_seconds=3600, max_count=100)
    state = store.get_or_create("xyz")
    state.messages.append({"role": "user", "content": "hi"})
    store.save(state)
    fresh = store.get_or_create("xyz")
    assert fresh.messages == [{"role": "user", "content": "hi"}]


def test_ttl_eviction_drops_idle_conversations(monkeypatch):
    fake_now = {"t": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: fake_now["t"])

    store = InMemoryConversationStore.create(max_age_seconds=60, max_count=100)
    store.get_or_create("idle")

    fake_now["t"] += 30  # within TTL
    store.get_or_create("active")
    assert "idle" in store._by_id

    fake_now["t"] += 200  # well past TTL since "idle" was last touched
    store.get_or_create("trigger")  # triggers a sweep

    assert "idle" not in store._by_id
    assert "active" not in store._by_id
    assert "trigger" in store._by_id


def test_capacity_cap_evicts_oldest_first(monkeypatch):
    fake_now = {"t": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: fake_now["t"])

    store = InMemoryConversationStore.create(max_age_seconds=3600, max_count=2)
    store.get_or_create("oldest")
    fake_now["t"] += 1
    store.get_or_create("middle")
    fake_now["t"] += 1
    store.get_or_create("newest")

    assert "oldest" not in store._by_id
    assert "middle" in store._by_id
    assert "newest" in store._by_id
