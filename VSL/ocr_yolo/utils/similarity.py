import re
def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text

def jaccard_similarity(text1, text2):
    set1, set2 = set(preprocess(text1).split()), set(preprocess(text2).split())
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union) if union else 0
