import os
import re
import requests
from time import time, sleep
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# YouTube Data API v3 key
API_KEY = 'AIzaSyD5cgmvzf15ksY5VsSZNituaXasG9DtlQE'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


# 5. Function to process the tunnel download (modified with error handling and retries)
def process_tunnel_download(tunnel_url, filename):
    """
    Processes the tunnel download with retries and file verification.
    Args:
        tunnel_url (str): The URL of the tunnel to download the video.
        filename (str): The name of the file to save the downloaded video.
    """
    mb = 1024 * 1024  # 1 MB in bytes
    MAX_RETRIES = 3
    retry_count = 0
    download_success = False

    while retry_count < MAX_RETRIES and not download_success:
        try:
            print(f"📥 Attempt {retry_count+1}/{MAX_RETRIES}: Downloading {filename}")
            response = requests.get(tunnel_url, stream=True)
            response.raise_for_status()  # Will throw HTTPError for bad status

            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 65536  # 64 KB chunk size for download
            if total == 0:
                print("⚠️ Warning: Content-Length is 0, proceeding with download using a 100mb file size(default).")
                total = 100 * mb  # Default to 100 MB if no content-length provided
            else:
                print(f"Total size: {total // mb} MB")
            start_time = time()

            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Progress display logic remains unchanged
                        if total:
                            percent = downloaded / total * 100
                            bar = f"[{'=' * int(percent // 2):50}] {percent:5.1f}%"
                        else:
                            bar = f"[{'=' * 50}] downloading..."
                        print(f"\r{bar} ({downloaded // 1024} KB)", end="")

            # Verify download integrity after completion
            file_size = os.path.getsize(filename)
            if file_size == 0:
                os.remove(filename)  # Clean up empty file
                raise ValueError("Downloaded file is 0 bytes - possibly incomplete")

            download_success = True
            print(f"\n✅ Download verified! Saved as '{filename}' ({file_size//1024} KB)")
            print(f"⏱️ Time taken: {int(time() - start_time)} seconds")

        except Exception as e:
            retry_count += 1
            # Clean up failed download
            if os.path.exists(filename):
                os.remove(filename)
                
            if retry_count < MAX_RETRIES:
                print(f"\n⚠️ Download failed: {str(e)} - Retrying...")
                sleep(2)  # Wait before retrying
            else:
                print(f"\n❌ FATAL: Download failed after {MAX_RETRIES} attempts. Last error: {str(e)}")
                return False

    return download_success

# 4. Function to process the tunnel download url for the video
def fn_getVid(title, url):
    """
    Processes the video download by sending a request to the tunnel URL.(cobalt)
    and calling the download function using the url returned.
    This function assumes that the tunnel URL is a valid endpoint that can handle
    Args:
        title (str): The title of the video.
        url (str): The URL of the video.
    """
    print(f"Processing video: {title} ({url})")
    endpoint = 'http://localhost:9000/'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = {
        'url': url,
        'videoQuality': "1080",
        'youtubeVideoCodec': "h264",
        'audioFormat': "best",
        'filenameStyle': "pretty"
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    
    # Handle response  - It should return a JSON with status and URL for the tunnel
    if response.status_code == 200:
            data = response.json()
            print("Yt Tunnel Successfully Obtained:", data)

            if data.get("status") == "tunnel":
                tunnel_url = data.get("url")
                filename = data.get("filename", f"{title}.mp4")  # Default to title if no filename provided
                if tunnel_url:
                    return process_tunnel_download(tunnel_url, filename)
                else:
                    print("Tunnel status received, but no URL provided.")
                    return False
            else:
                print("Unexpected status:", data.get("status"))
                return False

# 3. Function to process the videos data - calls above function for each video from the playlist data list dictionary provided
def process_videos(data):
    num = 0
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")

    videos = data.get('videos', [])
    print(f"Processing {len(videos)} videos...")
    if not isinstance(videos, list):
        raise ValueError("'videos' key must contain a list")
    
     # Track failed downloads
    failed_downloads = []
    failed_log = "failed_downloads.txt"

    for video in videos:
        print(f"\n{'='*40}")
        print(f"Processing video {num + 1} of {len(videos)}")
        num += 1

        if not isinstance(video, dict):
            print("⚠️ Skipping malformed video entry")
            continue  # skip malformed entries

        title = video.get('title')
        url = video.get('url')

        # Basic checks to ensure valid data
        if not title or not url:
            print(f"⚠️ Skipping invalid entry: Title={title}, URL={url}")
            continue

        try:
            # Attempt download and capture result
            success = fn_getVid(title, url)
            if not success:
                print(f"❌ Download failed for: {title}")
                failed_downloads.append({"title": title, "url": url})
        except Exception as e:
            print(f"🔥 Unexpected error downloading {title}: {str(e)}")
            failed_downloads.append({"title": title, "url": url, "error": str(e)})

    # Save failed downloads if any
    if failed_downloads:
        print(f"\n{'⚠️'*10} FAILURES DETECTED {'⚠️'*10}")
        print(f"{len(failed_downloads)} videos failed to download. Saving to {failed_log}")
        
        with open(failed_log, "w", encoding="utf-8") as f:
            f.write("Failed Video Downloads:\n\n")
            for item in failed_downloads:
                f.write(f"Title: {item['title']}\n")
                f.write(f"URL: {item['url']}\n")
                if 'error' in item:
                    f.write(f"Error: {item['error']}\n")
                f.write("-"*50 + "\n")
                
        print("✅ Failure log saved. You can retry these later")
    else:
        print("\n🎉 All videos downloaded successfully!")
    
    return failed_downloads

# 2. Function to extract playlist ID from various YouTube playlist URL formats
def get_playlist_id_from_url(playlist_url):
    """
    Extracts the playlist ID from various YouTube playlist URL formats.

    Args:
        playlist_url (str): The URL of the YouTube playlist.

    Returns:
        str: The playlist ID, or None if not found.
    """
    # Regex to find playlist ID in a URL
    # Handles URLs like:
    # https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxx
    # https://www.youtube.com/watch?v=VIDEO_ID&list=PLxxxxxxxxxxxxxxxxx
    # https://music.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxx
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|music\.youtube\.com)\/(?:playlist|watch)\?(?:.*&)?list=([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|music\.youtube\.com)\/embed\/videoseries\?list=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, playlist_url)
        if match:
            return match.group(1)
    print("Error: Could not extract playlist ID from the URL.")
    return None

# 1. Function to fetch and return video titles and URLs from a YouTube playlist
def get_playlist_videos_info(api_key, playlist_url):
    """
    Fetches the title and URL of each video in a YouTube playlist and returns them.

    Args:
        api_key (str): Your YouTube Data API v3 key.
        playlist_url (str): The URL of the YouTube playlist.

    Returns:
        dict: A dictionary containing 'total_videos' (int) and 'videos' (list of dicts),
              where each inner dict has 'title' and 'url'.
              Returns None if an error occurs (e.g., invalid API key, playlist not found).
    """
    if api_key == 'YOUR_API_KEY':
        print("Error: Please replace 'YOUR_API_KEY' with your actual API key in the script.")
        return None

    playlist_id = get_playlist_id_from_url(playlist_url)
    if not playlist_id:
        return None # Playlist ID could not be extracted

    videos_data = []
    video_count = 0
    next_page_token = None

    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=api_key)
        print(f"Fetching videos for playlist ID: {playlist_id}...") # Keep some feedback

        while True:
            # Request to get playlist items
            playlist_items_request = youtube.playlistItems().list(
                part='snippet,contentDetails',  # snippet contains title, resourceId (for videoId)
                                              # contentDetails contains videoId directly as well
                playlistId=playlist_id,
                maxResults=50,  # API allows max 50 results per page
                pageToken=next_page_token
            )
            playlist_items_response = playlist_items_request.execute()

            if not playlist_items_response.get('items'):
                if video_count == 0: # Only print if no items were ever found
                    print("No videos found in this playlist or the playlist is private/deleted.")
                break # Exit loop if no items on this page (or playlist empty)

            for item in playlist_items_response['items']:
                video_count += 1
                title = item['snippet']['title']
                video_id = item['snippet']['resourceId']['videoId']
                video_url = f'https://www.youtube.com/watch?v={video_id}' # Standard video URL

                videos_data.append({'title': title, 'url': video_url})

            next_page_token = playlist_items_response.get('nextPageToken')
            if not next_page_token:
                break  # No more pages

        if video_count > 0:
            print(f"Finished fetching. Total videos found: {video_count}\n")

        return {
            'total_videos': video_count,
            'videos': videos_data
        }

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content.decode("utf-8") if e.content else "No content"}')
        if e.resp.status == 403:
            print("This might be due to an invalid API key, or API quota exceeded, or the API not being enabled.")
        elif e.resp.status == 404:
            print("Playlist not found. Please check the playlist URL or ID.")
        return None # Return None on HTTP error
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return None # Return None on other exceptions  

# Main execution block
def main():
    # Get video data from playlist
    video_data = get_playlist_videos_info(API_KEY, playlist_url)
    
    # First attempt to download all videos
    initial_failures = process_videos(video_data)
    
    # If there were failures, automatically retry them
    if initial_failures:
        print("\n" + "⚠️" * 50)
        print(f"Initial run completed with {len(initial_failures)} failures")
        print("Starting automatic retry of failed downloads...")
        print("⚠️" * 50 + "\n")
        
        # Retry failed downloads
        retry_data = {'videos': initial_failures}
        retry_failures = process_videos(retry_data)
        
        if retry_failures:
            print("\n" + "❌" * 50)
            print(f"Could not download {len(retry_failures)} videos after retry:")
            for i, item in enumerate(retry_failures, 1):
                print(f"{i}. {item['title']}")
            print("Permanent failures saved in 'failed_downloads.txt'")
            print("❌" * 50)
        else:
            print("\n" + "🎉" * 50)
            print("All videos successfully downloaded on retry!")
            print("🎉" * 50)
            
            # Clean up success log if all succeeded on retry
            if os.path.exists("failed_downloads.txt"):
                os.remove("failed_downloads.txt")
    else:
        print("\n" + "✅" * 50)
        print("All videos downloaded successfully on first attempt!")
        print("✅" * 50)

if __name__ == '__main__':
    # set playlist url
 # Prompt user for playlist URL
    print("Please enter the YouTube playlist URL:")
    playlist_url = input().strip()  # Wait for user input and capture when Enter is pressed

    if API_KEY != 'YOUR_API_KEY':
            main()
    else:
        print("Please configure your API_KEY at the top of the script before running.")
