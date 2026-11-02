"""Upload an episode to YouTube with the YouTube Data API (title, description,
tags and thumbnail come from the script's Upload package).

One-time setup:
  1. In Google Cloud Console create a project, enable "YouTube Data API v3",
     create an OAuth client ID of type "Desktop app", download it as
     client_secret.json into this folder.
  2. pip install google-api-python-client google-auth-oauthlib
  3. The first run opens a browser to sign in to the channel; the token is
     saved to youtube-token.json (keep both files out of git).

Videos always go up as private (or scheduled with --publish-at) so you can
check them before anyone sees them.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def package(script_path):
    src = Path(script_path).read_text()
    pkg = src.split("## Upload package", 1)[1].split("## Full script", 1)[0]
    title = re.search(r"\*\*Title \(primary\):\*\*\s*(.+)", pkg).group(1).strip()
    desc = "\n".join(l[2:] if l.startswith("> ") else l.lstrip(">") for l in pkg.splitlines() if l.startswith(">")).strip()
    tags = re.search(r"\*\*Tags / keywords:\*\*\s*(.+)", pkg).group(1).split(",")
    return title[:100], desc, [t.strip() for t in tags if t.strip()]

def service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    tok = HERE / "youtube-token.json"
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES) if tok.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(str(HERE / "client_secret.json"), SCOPES).run_local_server(port=0)
        tok.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def upload(ep_dir, script_path, publish_at=None):
    from googleapiclient.http import MediaFileUpload
    ep_dir = Path(ep_dir)
    title, desc, tags = package(script_path)
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if publish_at:
        status["publishAt"] = publish_at
    yt = service()
    req = yt.videos().insert(part="snippet,status", body={
        "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "24"},  # 24 = Entertainment
        "status": status,
    }, media_body=MediaFileUpload(str(ep_dir / "video-16x9.mp4"), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    thumb = ep_dir / "thumbnail.png"
    if thumb.exists():
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
    print(f"uploaded: https://youtu.be/{vid} ({'scheduled ' + publish_at if publish_at else 'private'})")
    return vid

if __name__ == "__main__":
    upload(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
