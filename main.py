import json
import os
import shutil
import re
import subprocess
import yt_dlp
from mutagen.id3 import ID3, TIT2, TPE1, USLT, SYLT, APIC, Encoding
from mutagen.mp3 import MP3

# ------------ CONFIG ------------
JSON_FILE = "./data.json"
DOWNLOAD_DIR = "./downloads"
FINISHED_DIR = "./finished"
AUDIO_BITRATE = "320"  # kbps
MODEL_NAME = "llama3"  # Local LLM model name for Ollama
# --------------------------------

def load_json(file_path):
    return json.load(open(file_path, "r", encoding="utf-8")) if os.path.exists(file_path) else []

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def download_audio_and_captions(url):
    """Download YouTube audio (mp3) and English captions (srt)."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": AUDIO_BITRATE,
        }],
        "writesubtitles": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "srt",
        "writeautomaticsub": True,
        "quiet": False
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info["id"]
        title = info["title"]
        return {
            "id": video_id,
            "title": title,
            "mp3_path": os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3"),
            "captions_path": os.path.join(DOWNLOAD_DIR, f"{video_id}.en.srt"),
        }

def srt_to_sylt(srt_path):
    """Convert SRT file to SYLT-compatible list of (time_ms, text)."""
    if not os.path.exists(srt_path):
        return []

    entries = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")
    time_pattern = re.compile(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        time_line = lines[1]
        match = time_pattern.match(time_line)
        if not match:
            continue

        start_h, start_m, start_s, start_ms, _, _, _, _ = match.groups()
        start_time_ms = (
            int(start_h) * 3600000 +
            int(start_m) * 60000 +
            int(start_s) * 1000 +
            int(start_ms)
        )

        # Join remaining lines as caption text
        text = " ".join(lines[2:]).strip()
        if text:
            entries.append((start_time_ms, text))

    return entries

def srt_to_plain_lyrics(srt_path):
    """Convert SRT to plain unsynced lyrics as fallback."""
    if not os.path.exists(srt_path):
        return ""
    lyrics = []
    with open(srt_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().isdigit() or "-->" in line:
                continue
            if line.strip():
                lyrics.append(line.strip())
    return "\n".join(lyrics)

def query_local_llm(prompt):
    """Query local LLM (via Ollama)."""
    result = subprocess.run(["ollama", "run", MODEL_NAME],
                            input=prompt.encode("utf-8"),
                            capture_output=True)
    return result.stdout.decode("utf-8").strip()

def tag_mp3_with_sylt(mp3_path, cover_path, song_name, artists, sylt_entries, plain_lyrics):
    """Tag MP3 with song metadata, cover, and SYLT + USLT lyrics."""
    audio = MP3(mp3_path, ID3=ID3)
    if audio.tags is None:
        audio.add_tags()

    # Title + Artist
    audio.tags.add(TIT2(encoding=3, text=song_name))
    audio.tags.add(TPE1(encoding=3, text=artists))

    # Unsynced lyrics (fallback)
    if plain_lyrics:
        audio.tags.add(USLT(encoding=3, lang="eng", text=plain_lyrics))

    # Synced lyrics (SYLT)
    if sylt_entries:
        audio.tags.add(SYLT(
            encoding=Encoding.UTF8,
            lang="eng",
            format=2,  # ms time format
            type=1,    # lyrics
            desc="Lyrics",
            text=sylt_entries
        ))

    # Add cover
    if os.path.exists(cover_path):
        with open(cover_path, "rb") as img:
            audio.tags.add(APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=img.read()
            ))

    audio.save()

def safe_json_parse(llm_output, title):
    """Extract JSON object from LLM text output safely."""
    try:
        # Direct parse attempt
        return json.loads(llm_output)
    except json.JSONDecodeError:
        # Try to find the JSON substring with regex
        match = re.search(r"\{.*\}", llm_output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    # fallback
    return {"song": title, "artists": ["Unknown"]}

def process_song(yt_url, cover_path):
    """Full pipeline: download → LLM metadata → tag MP3 → save + update JSON."""
    data = load_json(JSON_FILE)
    print(f"Downloading: {yt_url}")
    result = download_audio_and_captions(yt_url)

    # Captions → SYLT + plain lyrics
    sylt_entries = srt_to_sylt(result["captions_path"])
    plain_lyrics = srt_to_plain_lyrics(result["captions_path"])

    # Prompt LLM for nice metadata
    print(f"Asking ai to clean title: {result['title']}")
    prompt = f"""
    The YouTube video title is: "{result['title']}".
    Give me a clean Spotify-style format:
    - Song Name
    - Artist(s)
    Return it in JSON: {{"song": "...", "artists": ["..."]}}
    """
    metadata = safe_json_parse(query_local_llm(prompt), result["title"])
    print(f"LLM output: {metadata}")

    song_name = metadata["song"]
    artists = metadata["artists"]

    # Tag MP3
    tag_mp3_with_sylt(result["mp3_path"], cover_path, song_name, artists, sylt_entries, plain_lyrics)

    # Move to finished folder
    os.makedirs(FINISHED_DIR, exist_ok=True)
    final_path = os.path.join(FINISHED_DIR, f"{song_name}.mp3")
    shutil.move(result["mp3_path"], final_path)

    # Update JSON
    new_entry = {
        "id": result["id"],
        "yt_url": yt_url,
        "cover_path": cover_path,
        "mp3_path": final_path,
        "captions_path": result["captions_path"],
        "status": "done",
        "song_name": song_name,
        "artists": artists
    }
    data.append(new_entry)
    save_json(JSON_FILE, data)

    print(f"✅ Finished: {song_name} by {', '.join(artists)}")

if __name__ == "__main__":
    yt_url = input("Enter YouTube URL: ").strip()
    cover_path = input("Enter cover image path: ").strip()
    process_song(yt_url, cover_path)
