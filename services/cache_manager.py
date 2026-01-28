import pickle
import hashlib
import os

class BytecodeCache:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_hash(self, source):
        return hashlib.md5(source.encode('utf-8')).hexdigest()

    def get(self, source):
        source_hash = self._get_hash(source)
        cache_file = os.path.join(self.cache_dir, f"{source_hash}.bin")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    return data['chunk'], data['functions']
            except Exception as e:
                print(f"Cache read error: {e}")
        return None, None

    def set(self, source, chunk, functions):
        source_hash = self._get_hash(source)
        cache_file = os.path.join(self.cache_dir, f"{source_hash}.bin")
        
        try:
            with open(cache_file, "wb") as f:
                pickle.dump({
                    'chunk': chunk,
                    'functions': functions
                }, f)
        except Exception as e:
            print(f"Cache write error: {e}")

    def clear(self):
        for file in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, file))

    def cleanup(self, max_age_days=7):
        """Removes cache files older than max_age_days."""
        import time
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        count = 0
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    count += 1
        if count > 0:
            print(f"Cleaned up {count} old cache files.")
