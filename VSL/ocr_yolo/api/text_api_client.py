import requests
import os
import time

class TextAPIClient:
    def __init__(self, base_url, rate_limiter, api_key):
        self.base_url = base_url
        self.rate_limiter = rate_limiter
        self.api_key = api_key

    def process_image(self, image_path, language="vnm"):
        """
        Gửi ảnh đến API OCR.Space và trả về text.
        Nếu API lỗi hoặc trả rỗng => nghỉ 7 phút rồi thử lại.
        """
        if not os.path.exists(image_path):
            print(f"[LỖI] Không tìm thấy ảnh: {image_path}")
            return ""

        while True:  # vòng lặp retry khi gặp lỗi
            self.rate_limiter.acquire()

            payload = {
                "apikey": self.api_key,
                "language": language,
                "isOverlayRequired": False,
                "OCREngine": 2,
            }

            try:
                with open(image_path, "rb") as f:
                    files = {"file": f}
                    response = requests.post(self.base_url, files=files, data=payload)
            except Exception as e:
                self.rate_limiter.wait_if_error(f"Lỗi request: {e}")
                continue  # thử lại

            if response.status_code != 200:
                self.rate_limiter.wait_if_error(f"HTTP {response.status_code}")
                continue  # thử lại

            try:
                result = response.json()
            except Exception:
                self.rate_limiter.wait_if_error("Không đọc được JSON từ API")
                continue  # thử lại

            parsed = result.get("ParsedResults", [])
            if parsed and isinstance(parsed, list) and len(parsed) > 0:
                text = parsed[0].get("ParsedText", "").strip()
                text_clean = text.replace("\n", " ")
                print(f"API result: {text_clean}")
                return text_clean
            else:
                print("[CẢNH BÁO] API không trả về ParsedResults hoặc rỗng.")
                self.rate_limiter.wait_if_error("ParsedResults rỗng")
                continue  # thử lại
