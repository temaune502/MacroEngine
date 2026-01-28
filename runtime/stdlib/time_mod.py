import time

def sleep(seconds, runtime_instance=None):
    """Smart sleep that allows processing events while waiting."""
    if runtime_instance is None:
        time.sleep(seconds)
        return
        
    end_time = time.time() + seconds
    while time.time() < end_time:
        if runtime_instance.should_exit:
            break
        runtime_instance.process_events()
        remaining = end_time - time.time()
        if remaining > 0.1:
            time.sleep(0.05)
        else:
            time.sleep(0.01)

class TimeWrapper:
    def __init__(self, runtime_instance=None):
        self.runtime = runtime_instance

    def sleep(self, secs):
        sleep(secs, self.runtime)

    def time(self): return time.time()
    def time_str(self): return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    def time_ms(self): return int(time.time() * 1000)
    def perfcount(self): return time.perf_counter()
