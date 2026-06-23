import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

def upload_video():
    client_id = os.getenv("YT_CLIENT_ID")
    client_secret = os.getenv("YT_CLIENT_SECRET")
    refresh_token = os.getenv("YT_REFRESH_TOKEN")

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
            "category_id": "22",
            "title": "Automated AI Video",
            "description": "This video was generated automatically.",
            "tags": ["AI", "Automation", "YouTube"]
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media_file = MediaFileUpload("final_video.mp4")

    response = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    ).execute()

    print(f"Video uploaded: https://www.youtube.com/watch?v={response['id']}")

if __name__ == "__main__":
    if os.path.exists("final_video.mp4"):
        upload_video()
    else:
        print("final_video.mp4 not found!")
