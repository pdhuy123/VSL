# VSL — Visual Sign Language (Project)

Mô tả ngắn: dự án VSL là một bộ công cụ xử lý video chữ ký (sign language) để trích xuất văn bản từ các video có chữ/ký hiệu và để làm tiền xử lý cho bài toán dịch ký hiệu sang text. Repository hiện bao gồm một module OCR với YOLO để crop vùng text và nhiều script phụ trợ cho việc trích xuất text từ video.

Mục tiêu của hướng dẫn này: mô tả cấu trúc hiện tại của project, đưa ra quy trình xử lý dữ liệu sử dụng MediaPipe để trích xuất keypoints từ từng frame, kiến trúc huấn luyện dự kiến (LSTM + CTC loss), và cung cấp mã ví dụ để bạn có thể triển khai pipeline huấn luyện và inference.

## Tổng quan kiến trúc đề xuất

- Input: video (người ký hiệu). Tách frame (ví dụ 25-30 fps) và chọn lại frame (frame sampling) để giảm độ dài chuỗi.
- Tiền xử lý: cho mỗi frame sử dụng MediaPipe (Hands, Pose, Face nếu cần) để trích xuất keypoints (x,y,visibility). Chuỗi các vector keypoint theo thời gian sẽ là input cho mô hình sequence.
- Mô hình: stack LSTM (hoặc BiLSTM) để học biểu diễn thời gian, theo sau là một dense layer -> softmax trên vocabulary (ký tự hoặc token). Sử dụng CTC loss để huấn luyện vì chiều dài input (frames) > chiều dài target (ký tự) và cần alignment tự động.
- Output: chuỗi ký tự (text). Dùng beam search hoặc greedy decoding để dự đoán từ xác suất của softmax.

## Cấu trúc file (quan trọng trong repository hiện tại)

- `ocr_yolo/` — module hiện tại để detect vùng chứa text trong video, gửi ảnh tới OCR API (ocr.space) và lưu kết quả JSON.
  - `config.py` — cấu hình API, tham số xử lý frame.
  - `main.py` — entrypoint để xử lý hàng loạt video.
  - `ocr/` — engine OCR (EasyOCR wrapper) và `ocr_manager.py` quản lý pipeline xử lý video.
  - `api/` — client gọi OCR API bên ngoài.
  - `utils/` — helper (file utils, rate limiter, similarity,...)

## Quy trình chi tiết (gợi ý triển khai LSTM + CTC)

1) Tách frames và trích xuất keypoints bằng MediaPipe

	- Cài đặt: `pip install mediapipe opencv-python numpy` (xem phần Dependencies).
	- Ví dụ: dùng MediaPipe Hands + Pose để lấy vị trí 2D hoặc normalized landmarks.

2) Tiền xử lý features

	- Với mỗi frame, lấy vector keypoints flatten [x1,y1,v1, x2,y2,v2, ...].
	- Chuẩn hóa (min-max hoặc z-score) theo dataset.
	- Pad hoặc truncate chuỗi frame để batch train (hoặc dùng packing + mask). LSTM có thể nhận sequences có chiều dài khác nhau nếu bạn dùng masking.

3) Mô hình: BiLSTM + Dense + softmax, huấn luyện với CTC

	- Input shape: (batch, time_steps, feature_dim)
	- Output logits: (batch, time_steps, vocab_size+1) (+1 cho blank token của CTC)
	- Sử dụng tensorflow/keras hoặc PyTorch. Dưới đây là mã ví dụ bằng TensorFlow/Keras.

## Dependencies (gợi ý)

- Python >= 3.8
- numpy, opencv-python, mediapipe
- tensorflow (>=2.8) hoặc pytorch
- easyocr (dự án hiện tại sử dụng EasyOCR cho OCR text), ultralytics (YOLO)
- requests (gọi API)

Ví dụ cài đặt nhanh (PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Và nội dung ví dụ `requirements.txt` có thể là:

```
numpy
opencv-python
mediapipe
tensorflow
easyocr
ultralytics
requests
```

## How to run (inference pipeline hiện có)

1. Đặt API key OCR vào file `.env` hoặc biến môi trường theo `ocr_yolo/.env.example`.
2. Đặt video vào `ocr_yolo/videos/`.
3. Chạy `python ocr_yolo/main.py` (PowerShell) để xử lý hàng loạt video và lưu JSON output vào `ocr_yolo/outputs/`.

## Gợi ý mở rộng để bài toán Sign Language -> Text

- Thay vì phát hiện text (OCR), thay `ocr_manager` bằng module MediaPipe keypoint extractor để trích xuất hands/pose landmarks cho mỗi frame.
- Tạo bộ dữ liệu mapping video -> label (chuỗi ký tự). Hiện repo có `saved_models`, `processed/` chứa một số mô hình LSTM/seq2seq pretrained — bạn có thể tham khảo `processed/lstm_sentence_model.h5`.
- Sử dụng tokenization phù hợp (character-level hoặc subword). Với CTC, thường dùng character-level.
- Thử nghiệm với augmentation (temporal cropping, speed change) để tăng tính bền vững.

## Next steps đề xuất

1. Tạo module tiền xử lý `vsl_pipeline/` (ví dụ code trên) và một `train.py` để chuẩn hóa data -> dataset -> train.
2. Viết file `requirements.txt` và notebook `training.ipynb` (repo hiện có `training.ipynb`) để minh họa quá trình.
3. Thêm script inference `predict.py` để chạy model trên 1 video và in ra kết quả.

Nếu bạn muốn, tôi có thể tiếp tục và:
- Tạo các file `vsl_pipeline/preprocess.py`, `vsl_pipeline/model_ctc.py`, `train.py`, `predict.py` với mã đầy đủ hơn.
- Thêm `requirements.txt` và cập nhật `VSL/README.md` thêm ví dụ chạy và test.

---

Tôi đã đọc cấu trúc hiện tại của `ocr_yolo/` và viết README này theo hướng mở rộng cho bài toán dịch ký hiệu bằng LSTM+CTC. Bạn muốn tôi tự động tạo các file mã ví dụ (`vsl_pipeline/*`, `train.py`, `requirements.txt`) trong repository không? Nếu có, tôi sẽ thêm tiếp và chạy kiểm tra nhanh môi trường Python (nếu cần).
