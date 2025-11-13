import easyocr

class EasyOCREngine:
    def __init__(self, languages=['vi']):
        self.reader = easyocr.Reader(languages, gpu = True)

    def detect_text(self, image):
        results = self.reader.readtext(image)
        texts = [res[1] for res in results]
        return texts
