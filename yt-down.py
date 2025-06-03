import requests
from time import time

# Simulated API response
response_data = {
    "status": "tunnel",
    "url": "http://localhost:9000/tunnel?id=mpHFAXh3SWCx-AxxkGlDP&exp=1748078387842&sig=EmJ-J826TB48lc0pCP_Ro-1sk5cZcMYWJYgy0muXE6I&sec=uNHE1cAsqnoMqirG2LUGJQuZtK-D33q6kR_05lUlk4I&iv=bQ918PRMAzf8m-JAXLrQYw",
    "filename": "The Fall of HUKU YUES What Happened - Ongori Reports (720p, h264, youtube).mp4"
}

def download_file_from_response(data):
    status = data.get("status")
    if status != "tunnel":
        print(f"⚠️ Unexpected status: {status}")
        return

    download_url = data["url"]
    filename = data.get("filename", "downloaded_file.mp4")

    print(f"📥 Starting download: {filename}")
    print(f"🔗 URL: {download_url}")

    response = requests.get(download_url, stream=True)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    chunk_size = 8192
    start_time = time()

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    percent = downloaded / total * 100
                    bar = f"[{'=' * int(percent // 2):50}] {percent:5.1f}%"
                else:
                    bar = f"[{'=' * 50}] downloading..."
                print(f"\r{bar} ({downloaded // 1024} KB)", end="")

    print(f"\n✅ Download complete! Saved as '{filename}'")
    print(f"⏱️ Time taken: {int(time() - start_time)} seconds")

# Run the download
download_file_from_response(response_data)
