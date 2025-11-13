import time
import os

class APIRateLimiter:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.request_times = []
        self.request_count = 0

    def acquire(self):
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < self.window]

        if len(self.request_times) >= self.limit:
            sleep_time = self.window - (now - self.request_times[0])
            print(f"\nĐạt giới hạn {self.limit} request/{self.window}s.")
            print(f"Nghỉ {sleep_time:.1f} giây (~{sleep_time/60:.1f} phút)...")
            time.sleep(sleep_time)
            self.request_times = []
            self.request_count = 0

        self.request_times.append(time.time())
        self.request_count += 1
        print(f"Request thứ {self.request_count}")

    def wait_if_error(self, message=None):
        print("\nAPI lỗi hoặc không trả kết quả hợp lệ — nghỉ 7 phút rồi thử lại.")
        if message:
            print(f"Chi tiết lỗi: {message}")
        time.sleep(420) 
        print("Hết thời gian nghỉ, thử lại request này...")
        self.request_times = [t for t in self.request_times if time.time() - t < self.window]
