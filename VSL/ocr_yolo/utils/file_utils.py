import os
import json
import csv
import cv2

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def list_video_files(folder, extensions=(".mp4", ".avi", ".mov")):
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(extensions)
    ]

def save_results_to_json(results, output_path):
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu kết quả JSON: {output_path}")

def extract_frame(video_path, frame_interval=30):
    cap = cv2.VideoCapture(video_path)
    frames = []
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            frames.append(frame)
        count += 1

    cap.release()
    return frames
