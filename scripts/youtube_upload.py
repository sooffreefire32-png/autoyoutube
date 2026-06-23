import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from datetime import datetime

UPLOAD_COUNT_FILE = "daily_upload_count.json"

def get_daily_upload_count():
    if os.path.exists(UPLOAD_COUNT_FILE):
        with open(UPLOAD_COUNT_FILE, "r") as f:
            data = json.load(f)
            today = datetime.now().strftime("%Y-%m-%d")
            if data.get("date") == today:
                return data.get("count", 0)
    return 0

def increment_daily_upload_count():
    count = get_daily_upload_count()
    today = datetime.now().strftime("%Y-%m-%d")
    with open(UPLOAD_COUNT_FILE, "w") as f:
        json.dump({"date": today, "count": count + 1}, f)

def upload_video():
    # Load secrets
    client_id = os.getenv("YT_CLIENT_ID")
    client_secret = os.getenv("YT_CLIENT_SECRET")
    refresh_token = os.getenv("YT_REFRESH_TOKEN")
    max_daily_uploads = int(os.getenv("MAX_DAILY_UPLOADS", 6)) # Default to 6 if not set

    # Check daily upload limit
    current_uploads = get_daily_upload_count()
    if current_uploads >= max_daily_uploads:
        print(f"Daily upload limit of {max_daily_uploads} reached. Skipping upload.")
        return

    # Load video metadata
    metadata_path = "video_metadata.json"
    if not os.path.exists(metadata_path):
        print("video_metadata.json not found!")
        return
    with open(metadata_path, "r", encoding="utf-8") as f:
        video_metadata = json.load(f)

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )

    youtube = build("youtube", "v3", credentials=creds)

    request_body = {
        "snippet": {
            "categoryId": "22", # Default category for 'Howto & Style'
            "title": video_metadata.get("title", "Automated AI Video"),
            "description": video_metadata.get("description", "This video was generated automatically."),
            "tags": video_metadata.get("tags", ["AI", "Automation", "YouTube"])
        },
        "status": {
            "privacyStatus": "public" # Can be 'public', 'private', or 'unlisted'
        }
    }

    video_file = "final_video.mp4"
    if not os.path.exists(video_file):
        print(f"{video_file} not found!")
        return

    media_body = MediaFileUpload(video_file)

    print(f"Uploading video: {request_body['snippet']['title']}")
    try:
        response = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_body
        ).execute()

        video_id = response["id"]
        print(f"Video uploaded: https://www.youtube.com/watch?v={video_id}")
        increment_daily_upload_count() # Increment count only on successful upload

        # Upload thumbnail if available
        thumbnail_path = "assets/thumbnail.jpg" # User specified thumbnail.jpg in assets folder
        if os.path.exists(thumbnail_path):
            print(f"Uploading thumbnail from {thumbnail_path}")
            media_thumbnail = MediaFileUpload(thumbnail_path)
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=media_thumbnail
            ).execute()
            print("Thumbnail uploaded.")
        else:
            print(f"Thumbnail file not found at {thumbnail_path}. Skipping thumbnail upload.")
    except Exception as e:
        print(f"Error during YouTube upload: {e}")

if __name__ == "__main__":
    upload_video()
