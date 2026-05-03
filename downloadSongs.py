import yt_dlp
import os

PLAYLIST_URL = input("Enter YouTube Music playlist URL: ").strip()
OUTPUT_DIR = input("Enter output folder (default: downloads): ").strip() or "downloads"

os.makedirs(OUTPUT_DIR, exist_ok=True)

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join(OUTPUT_DIR, '%(playlist_index)s - %(title)s.%(ext)s'),

    # Extract audio
    'postprocessors': [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        },
        {
            'key': 'FFmpegMetadata',  # embed metadata
        },
        {
            'key': 'EmbedThumbnail',  # album art
        }
    ],

    # Metadata handling
    'writethumbnail': True,
    'addmetadata': True,

    # Better naming metadata from YT Music
    'metadata_from_title': '%(artist)s - %(title)s',

    # Playlist handling
    'ignoreerrors': True,
    'quiet': False,
    'noplaylist': False,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([PLAYLIST_URL])

