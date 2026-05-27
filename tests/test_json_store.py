from promotion_collector.models import BusinessRecord
from promotion_collector.storage.json_store import JsonStore


def test_json_store_appends_only_unique_records(tmp_path) -> None:
    store = JsonStore(tmp_path / "records.json")
    first = BusinessRecord(
        name="Русское кафе",
        business_type="Ресторан / кафе",
        city="Nha Trang",
        website="https://example.com",
        source_url="https://osm.org/node/1",
    )
    duplicate = BusinessRecord(
        name="Русское кафе",
        business_type="Ресторан / кафе",
        city="Nha Trang",
        website="https://example.com",
        source_url="https://osm.org/node/2",
    )

    assert store.append_unique([first]) == [first]
    assert store.append_unique([duplicate]) == []
    assert len(store.load_records()) == 1
