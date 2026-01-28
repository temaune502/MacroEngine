import os
import json
import time

class StorageWrapper:
    def __init__(self, macro_name):
        self.macro_name = macro_name
        self.storage_dir = "storage"
        self.max_keys = 100
        self.max_val_size = 1024 * 10
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        safe_name = "".join([c if c.isalnum() else "_" for c in macro_name])
        self.file_path = os.path.join(self.storage_dir, f"{safe_name}.json")
        self._cache = self._load_file()
        self._last_saved_cache = json.dumps(self._cache, sort_keys=True)
        self._last_sync_time = time.time()
        self._sync_interval = 5.0
        self._auto_save = True
        
    def _load_file(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def _sync(self, force=False):
        if not self._auto_save and not force:
            return
        current_time = time.time()
        if force or (current_time - self._last_sync_time >= self._sync_interval):
            current_cache_str = json.dumps(self._cache, sort_keys=True)
            if current_cache_str != self._last_saved_cache:
                try:
                    with open(self.file_path, "w", encoding="utf-8") as f:
                        f.write(current_cache_str)
                    self._last_saved_cache = current_cache_str
                except:
                    pass
            self._last_sync_time = current_time

    def set_config(self, interval=None, auto_save=None):
        if interval is not None: self._sync_interval = float(interval)
        if auto_save is not None: self._auto_save = bool(auto_save)
            
    def save(self): self._sync(force=True)

    def write(self, key, value):
        if len(self._cache) >= self.max_keys and str(key) not in self._cache:
            return False
        val_str = json.dumps(value)
        if len(val_str) > self.max_val_size:
            return False
        self._cache[str(key)] = value
        if self._auto_save: self._sync()
        return True

    def read(self, key, default=None):
        self._sync()
        return self._cache.get(str(key), default)

    def has(self, key):
        self._sync()
        return str(key) in self._cache

    def delete(self, key):
        k = str(key)
        if k in self._cache:
            del self._cache[k]
            self._sync()
            return True
        return False

    def clear(self):
        self._cache = {}
        self._sync()
