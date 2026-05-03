import os
import requests
import re
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

def scan_folder(path):
    """Scans the given path for audio files."""
    audio_extensions = ('.mp3', '.wav', '.ogg')
    files = []
    if os.path.exists(path):
        for file in os.listdir(path):
            if file.lower().endswith(audio_extensions):
                files.append(os.path.join(path, file))
    return sorted(files)

def get_metadata(file_path):
    """Extracts metadata from an audio file."""
    metadata = {
        'title': os.path.basename(file_path),
        'artist': 'Unknown Artist',
        'album': 'Unknown Album',
        'duration': 0,
        'path': file_path
    }
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        audio = None
        
        if ext == '.mp3':
            audio = MP3(file_path)
            if audio.tags:
                metadata['title'] = str(audio.tags.get('TIT2', metadata['title']))
                metadata['artist'] = str(audio.tags.get('TPE1', metadata['artist']))
                metadata['album'] = str(audio.tags.get('TALB', metadata['album']))
        elif ext == '.ogg':
            audio = OggVorbis(file_path)
            metadata['title'] = audio.get('title', [metadata['title']])[0]
            metadata['artist'] = audio.get('artist', [metadata['artist']])[0]
            metadata['album'] = audio.get('album', [metadata['album']])[0]
        elif ext == '.wav':
            audio = WAVE(file_path)
        # Note: webm metadata extraction is complex without heavy libs, 
        # using filename as fallback which is already in metadata['title']
            
        if audio:
            metadata['duration'] = int(audio.info.length)
            
    except Exception as e:
        print(f"Error reading metadata for {file_path}: {e}")
        
    return metadata

def format_time(seconds):
    """Formats seconds into MM:SS."""
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes:02d}:{seconds:02d}"

class LyricsService:
    @staticmethod
    def fetch_lyrics(track_name, artist_name, album_name="", duration=0):
        """Fetches synced lyrics from LRCLIB."""
        url = "https://lrclib.net/api/get"
        params = {
            "track_name": track_name,
            "artist_name": artist_name,
            "album_name": album_name,
            "duration": duration
        }
        headers = {"User-Agent": "ModernMusicPlayer/1.0"}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('syncedLyrics', data.get('plainLyrics', ""))
            else:
                # Fallback to search if exact match fails
                search_url = "https://lrclib.net/api/search"
                search_params = {"q": f"{track_name} {artist_name}"}
                search_res = requests.get(search_url, params=search_params, headers=headers, timeout=5)
                if search_res.status_code == 200:
                    results = search_res.json()
                    if results:
                        return results[0].get('syncedLyrics', results[0].get('plainLyrics', ""))
        except Exception as e:
            print(f"Lyrics fetch error: {e}")
        return ""

    @staticmethod
    def parse_lrc(lrc_text):
        """Parses LRC format into a list of (timestamp_in_seconds, text)."""
        if not lrc_text: return []
        
        lines = lrc_text.splitlines()
        parsed = []
        pattern = re.compile(r'\[(\d+):(\d+\.\d+)\](.*)')
        
        for line in lines:
            match = pattern.match(line)
            if match:
                m, s, text = match.groups()
                timestamp = int(m) * 60 + float(s)
                parsed.append((timestamp, text.strip()))
        return parsed
