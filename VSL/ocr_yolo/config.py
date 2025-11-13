import dotenv, os
dotenv.load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OCR_API_KEYS = os.getenv("OCR_API")
LANGUAGES = ['vi']
SIMILARITY_THRESHOLD = 0.8
API_BASE_URL = "https://api.ocr.space/parse/image"
API_RATE_LIMIT = 180
API_WINDOW_SEC = 3600
VIDEO_FOLDER = os.path.join(BASE_DIR, "videos")
OUTPUT_FOLDER = "outputs"
CROP_HEIGHT_FACTOR = 0.7
FRAME_INTERVAL = 30
