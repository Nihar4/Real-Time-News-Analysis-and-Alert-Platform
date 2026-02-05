import json
import os
from typing import Set, Dict, Any
from datetime import datetime
import redis
from ..settings import settings

class DedupeStore:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.seen_ids: Set[str] = set()
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    self.seen_ids = set(data.get('seen_ids', []))
            except (json.JSONDecodeError, KeyError):
                self.seen_ids = set()

    def save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump({'seen_ids': list(self.seen_ids)}, f)

    def seen(self, item_id: str) -> bool:
        if item_id in self.seen_ids:
            return True
        self.seen_ids.add(item_id)
        self.save()
        return False

class RedisDedupeStore:
    def __init__(self, host: str, port: int, db: int):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def seen(self, item_id: str) -> bool:
        # Returns 1 if key was set (new), 0 if key existed
        # We want: True if seen (key existed), False if new (key was set)
        is_new = self.redis.setnx(f"seen:{item_id}", datetime.now().isoformat())
        return not is_new

class FeedHTTPState:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.state: Dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.state = json.load(f)
            except (json.JSONDecodeError, KeyError):
                self.state = {}

    def save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w') as f:
            json.dump(self.state, f)

    def get_last_modified(self, url: str) -> str:
        return self.state.get(url, {}).get('last_modified', '')

    def set_last_modified(self, url: str, last_modified: str):
        if url not in self.state:
            self.state[url] = {}
        self.state[url]['last_modified'] = last_modified
        self.state[url]['last_fetch'] = datetime.now().isoformat()
        self.save()
