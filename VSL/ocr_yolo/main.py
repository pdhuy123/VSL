import time
import os
import shutil
from utils.rate_limiter import APIRateLimiter
from ocr.easyocr_engine import EasyOCREngine
from api.text_api_client import TextAPIClient
from ocr.ocr_manager import OCRManager
from ultralytics import YOLO
from utils.file_utils import list_video_files, save_results_to_json
import config

yolo_model = YOLO("yolov8n.pt")

if __name__ == "__main__":
    rate_limiter = APIRateLimiter(limit=config.API_RATE_LIMIT, 
                                  window=config.API_WINDOW_SEC)
    ocr_engine = EasyOCREngine(languages=config.LANGUAGES)
    api_client = TextAPIClient(base_url=config.API_BASE_URL,
                               api_key=config.OCR_API_KEYS,
                               rate_limiter=rate_limiter)
    ocr_manager = OCRManager(ocr_engine, 
                             api_client,
                             yolo_model,
                             crop_height_factor=config.CROP_HEIGHT_FACTOR,
                             similarity_threshold=config.SIMILARITY_THRESHOLD,
                             frame_interval=config.FRAME_INTERVAL)

    videos = list_video_files(config.VIDEO_FOLDER)
    total_videos = len(videos)

    print(f"Tìm thấy {total_videos} video cần xử lý.\n")

    done_folder = os.path.join(config.VIDEO_FOLDER, "done")
    os.makedirs(done_folder, exist_ok=True)

    for idx, video_path in enumerate(videos, start=1):
        print(f"\n==============================")
        print(f"Video {idx}/{total_videos}: {os.path.basename(video_path)}")
        print(f"==============================")

        start_total = time.time()
        try:
            results = ocr_manager.process_video(video_path)
            output_name = os.path.splitext(os.path.basename(video_path))[0]
            output_json = f"{config.OUTPUT_FOLDER}/{output_name}.json"
            save_results_to_json(results, output_json)

            print(f"Hoàn tất video {idx}/{total_videos} ({time.time() - start_total:.2f}s)")

            done_path = os.path.join(done_folder, os.path.basename(video_path))
            shutil.move(video_path, done_path)
            print(f"Đã chuyển video sang thư mục 'done': {done_path}")

        except Exception as e:
            print(f"[LỖI] Khi xử lý video {os.path.basename(video_path)}: {e}")
            print("Bỏ qua và tiếp tục video tiếp theo...\n")
            continue

    print("\nĐã xử lý xong tất cả video.")
