import cv2
import os
import time
from utils.similarity import jaccard_similarity, preprocess

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

class OCRManager:
    def __init__(self, ocr_engine, api_client, yolo_model=None, similarity_threshold=0.9,
                 crop_height_factor=0.7, frame_interval=30):
        self.ocr_engine = ocr_engine
        self.api_client = api_client
        self.yolo_model = yolo_model
        self.similarity_threshold = similarity_threshold
        self.crop_height_factor = crop_height_factor
        self.frame_interval = frame_interval

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_id = 0

        last_text = ""
        last_api_text = ""          
        last_api_result = None      
        segment = None
        results = []
        temp_path = "temp_frame.jpg"
        last_processed_frame = -self.frame_interval

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = frame_id / fps

            if frame_id - last_processed_frame >= self.frame_interval:
                h, w = frame.shape[:2]
                x1, x2 = 0, w
                y1, y2 = int(h * self.crop_height_factor), h
                cropped = frame[y1:y2, x1:x2]

                texts = self.ocr_engine.detect_text(cropped)
                if not texts:
                    frame_id += 1
                    last_processed_frame = frame_id
                    continue

                current_text = preprocess(" ".join(texts).strip())
                sim = jaccard_similarity(current_text, last_text)
                last_processed_frame = frame_id

                largest_box = None
                if self.yolo_model:
                    yolo_results = self.yolo_model(frame, verbose=False)
                    max_area = 0
                    for r in yolo_results:
                        for box, cls in zip(r.boxes.xyxy, r.boxes.cls):
                            if int(cls) == 0:
                                bx1, by1, bx2, by2 = [int(v) for v in box.tolist()]
                                area = (bx2 - bx1) * (by2 - by1)
                                if area > max_area:
                                    max_area = area
                                    largest_box = [bx1, by1, bx2, by2]

                    if largest_box is None:
                        last_text = current_text
                        frame_id += 1
                        continue

                if sim < self.similarity_threshold:

                    if segment and segment.get("largest_box") is not None:
                        segment["end"] = format_time(current_time)
                        results.append(segment)

                    cv2.imwrite(temp_path, cropped)
                    api_result = self.api_client.process_image(temp_path)
                    print(f"API result: {api_result}")
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass

                    api_text = ""
                    if isinstance(api_result, str):
                        api_text = preprocess(api_result.strip())
                    elif isinstance(api_result, dict):
                        possible_keys = ['text', 'result', 'ocr_text', 'transcript']
                        found = False
                        for k in possible_keys:
                            if k in api_result and isinstance(api_result[k], str):
                                api_text = preprocess(api_result[k].strip())
                                found = True
                                break
                        if not found:
                            api_text = preprocess(str(api_result).strip())
                    else:
                        api_text = preprocess(str(api_result).strip())
                    api_sim = jaccard_similarity(api_text, last_api_text)

                    if api_sim >= self.similarity_threshold:
                        if segment and segment.get("largest_box") is not None:
                            segment["end"] = format_time(current_time)
                        else:

                            pass
                    else:
                        segment = {
                            "video_id": os.path.basename(video_path),
                            "start": format_time(current_time),
                            "end": None,
                            "api_result": api_result,
                            "largest_box": largest_box
                        }

                    last_api_text = api_text
                    last_api_result = api_result

                else:
                    if segment and segment.get("largest_box") is not None:
                        segment["largest_box"] = largest_box
                        segment["end"] = format_time(current_time)

                last_text = current_text
            else:
                if segment and segment.get("largest_box") is not None:
                    segment["end"] = format_time(current_time)

            frame_id += 1

        if segment and segment.get("largest_box") is not None:
            segment["end"] = format_time(total_frames / fps)
            results.append(segment)

        cap.release()
        return results
