from opsguardian.models import Incident
from opsguardian.storage import DynamoDBStore


class FakePaginatedTable:
    def __init__(self, pages):
        self.pages = pages
        self.calls = 0

    def scan(self, **kwargs):
        page = self.pages[self.calls]
        self.calls += 1
        return page


def test_dynamodb_list_reads_all_pages_before_sorting():
    old = Incident(id="old", updated_at="2026-08-20T00:00:00+00:00")
    newest = Incident(id="new", updated_at="2026-08-22T00:00:00+00:00")
    middle = Incident(id="mid", updated_at="2026-08-21T00:00:00+00:00")
    store = DynamoDBStore.__new__(DynamoDBStore)
    store.table = FakePaginatedTable(
        [
            {
                "Items": [
                    {"incident_id": old.id, "updated_at": old.updated_at, "payload": old.model_dump_json()},
                ],
                "LastEvaluatedKey": {"incident_id": old.id},
            },
            {
                "Items": [
                    {"incident_id": newest.id, "updated_at": newest.updated_at, "payload": newest.model_dump_json()},
                    {"incident_id": middle.id, "updated_at": middle.updated_at, "payload": middle.model_dump_json()},
                ]
            },
        ]
    )

    assert [item.id for item in store.list(limit=2)] == ["new", "mid"]
    assert store.table.calls == 2
