import yt_dlp
'''
with open("data.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]
'''
urls = ["nrCyWGFwEEI"] 
ydl_opts = {
    "format": "best",
    "outtmpl": "test/%(id)s.%(ext)s",
    "user_agent": "Mozilla/5.0"
}

failed_videos = []  
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    for url in urls:
        print(f"🔹 Đang tải: {url}")
        try:
            result = ydl.download([url])
            if result != 0:
                print(f"Lỗi tải: {url}")
                failed_videos.append(url)
        except Exception as e:
            print(f"Lỗi tải: {url} — {e}")
            failed_videos.append(url)

if failed_videos:
    print("\nCác video tải không thành công:")
    for fail in failed_videos:
        print(f" - {fail}")
else:
    print("\nTất cả video đã tải thành công!")
