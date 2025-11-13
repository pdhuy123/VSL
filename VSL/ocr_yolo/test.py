# create_dataset_from_json_strpaths.py
import os
import glob
import json
import subprocess
import shutil
import sys
from datetime import timedelta

JSON_FOLDER = "outputs"     
VIDEOS_DIR  = "videos/done"       
OUT_DIR     = "clips_out"   
DATASET_JSON = "dataset.json"
START_INDEX = 1

# optional OpenCV fallback
try:
    import cv2
    OPENCV_AVAILABLE = True
except Exception:
    OPENCV_AVAILABLE = False

os.makedirs(OUT_DIR, exist_ok=True)

def parse_time_hms(s):
    parts = s.split(":")
    parts = [int(p) for p in parts]
    if len(parts) == 3:
        h, m, sec = parts
    elif len(parts) == 2:
        h = 0
        m, sec = parts
    else:
        raise ValueError(f"Không hiểu định dạng thời gian: {s}")
    return timedelta(hours=h, minutes=m, seconds=sec)

def td_to_seconds(td: timedelta):
    return td.total_seconds()

def safe_int(x):
    try:
        return int(x)
    except:
        return None

FFMPEG_BIN = shutil.which("ffmpeg")
if FFMPEG_BIN:
    print(f"[INFO] Found ffmpeg: {FFMPEG_BIN}")
else:
    print("[WARN] ffmpeg không có trong PATH.")
    if not OPENCV_AVAILABLE:
        print("[ERR] OpenCV cũng không có. Cài ffmpeg hoặc opencv rồi chạy lại.")
        sys.exit(1)
    else:
        print("[INFO] Sẽ dùng OpenCV làm fallback (không giữ audio).")

mapping = {}
counter = START_INDEX

json_files = sorted(glob.glob(os.path.join(JSON_FOLDER, "*.json")))
if not json_files:
    print(f"[WARN] Không tìm thấy file json trong '{JSON_FOLDER}'")
for json_path in json_files:
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[WARN] Không đọc được {json_path}: {e}")
        continue

    if not isinstance(data, list):
        print(f"[WARN] {json_path} không chứa list, bỏ qua.")
        continue

    for entry in data:
        video_id = entry.get("video_id")
        start_s = entry.get("start")
        end_s   = entry.get("end")
        label   = entry.get("api_result") or entry.get("text") or ""
        largest = entry.get("largest_box")

        if not (video_id and start_s and end_s and largest):
            print(f"[SKIP] Thiếu trường video_id/start/end/largest_box trong {json_path} entry.")
            continue

        input_video = os.path.join(VIDEOS_DIR, video_id)
        if not os.path.exists(input_video):
            print(f"[SKIP] Không tìm thấy video gốc: {input_video}")
            continue

        try:
            t_start = parse_time_hms(start_s)
            t_end   = parse_time_hms(end_s)
        except Exception as e:
            print(f"[SKIP] Lỗi parse thời gian {start_s}/{end_s}: {e}")
            continue

        dur_td = t_end - t_start
        if dur_td.total_seconds() <= 0:
            print(f"[SKIP] Thời lượng <=0 cho {video_id} {start_s}-{end_s}")
            continue

        if (not isinstance(largest, (list, tuple))) or len(largest) < 4:
            print(f"[SKIP] largest_box không hợp lệ: {largest}")
            continue

        xmin = safe_int(largest[0]); ymin = safe_int(largest[1])
        xmax = safe_int(largest[2]); ymax = safe_int(largest[3])
        if None in (xmin, ymin, xmax, ymax):
            print(f"[SKIP] largest_box chứa giá trị không phải số: {largest}")
            continue

        w = xmax - xmin
        h = ymax - ymin
        if w <= 0 or h <= 0:
            print(f"[SKIP] largest_box kích thước không hợp lệ: {largest}")
            continue

        name = f"{counter:04d}.mp4"
        out_file = os.path.join(OUT_DIR, name)

        start_seconds = td_to_seconds(t_start)
        duration_seconds = td_to_seconds(dur_td)

        if FFMPEG_BIN:
            crop_filter = f"crop={w}:{h}:{xmin}:{ymin}"
            cmd = [
                FFMPEG_BIN,
                "-y",
                "-ss", str(start_seconds),
                "-i", input_video,
                "-t", str(duration_seconds),
                "-vf", crop_filter,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                out_file
            ]
            print(f"[RUN] Tạo {out_file} từ {input_video} {start_s}->{end_s} crop={w}x{h}+{xmin}+{ymin} bằng ffmpeg")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"[ERR] ffmpeg lỗi cho {video_id}: {e}")
                continue
        else:
            # OpenCV fallback (no audio)
            if not OPENCV_AVAILABLE:
                print("[SKIP] Không có ffmpeg và OpenCV -> bỏ qua.")
                continue
            print(f"[RUN] Tạo {out_file} từ {input_video} {start_s}->{end_s} crop={w}x{h}+{xmin}+{ymin} bằng OpenCV (no audio)")
            cap = cv2.VideoCapture(input_video)
            if not cap.isOpened():
                print(f"[ERR] OpenCV không mở được {input_video}")
                continue
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # clamp crop nếu vượt ranh giới
            xmin2 = max(0, xmin); ymin2 = max(0, ymin)
            if xmin2 + w > vid_w:
                w = max(1, vid_w - xmin2)
            if ymin2 + h > vid_h:
                h = max(1, vid_h - ymin2)

            start_frame = int(start_seconds * fps)
            end_frame = int((start_seconds + duration_seconds) * fps)
            start_frame = max(0, start_frame)
            end_frame = min(total_frames - 1, end_frame)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out_writer = cv2.VideoWriter(out_file, fourcc, fps, (w, h))
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            cur = start_frame
            while cur <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                crop = frame[ymin2:ymin2 + h, xmin2:xmin2 + w]
                if crop.size == 0:
                    break
                out_writer.write(crop)
                cur += 1
            cap.release()
            out_writer.release()

        mapping[name] = label
        counter += 1

# write dataset.json
with open(DATASET_JSON, "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Hoàn tất. Tạo {len(mapping)} clip. Dataset lưu tại '{DATASET_JSON}'. Video lưu trong '{OUT_DIR}'")
