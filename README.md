# 🎵 Tube2Tune

🎵 A **Python-powered script** that transforms YouTube videos into **MP3 tracks** — complete with **album cover art 🖼️, synced lyrics 🎤, and polished metadata ✨**.  

💡 Built for the **sole purpose** of enjoying your favorite **fan-made songs 💜** in music players like **Spotify 🎧, Prime Music 🔥, Wynk 🎶, and more!**  

## ✨ Features
- 🎥 Download audio from YouTube  
- 🎶 Convert to **high-quality MP3** (320kbps VBR)  
- 📝 Extract YouTube captions and embed them as **synchronized lyrics (SYLT)**  
- 🖼️ Add custom **album cover image** from local path  
- 🤖 Use a **local LLM** to clean up video titles into proper **Song Name + Artist(s)**  
- 🏷️ Auto-tag final MP3 with song name, artist(s), cover art, and lyrics  
- 📁 Organize into `finished/` folder for ready-to-import Spotify/iTunes library  
- 📜 JSON log file to keep track of processed videos  

---

## 📂 Project Structure
```
tube2tune/
│── downloads/        # temp storage (auto-cleaned)
│── finished/         # final MP3 files with tags
│── covers/           # album cover images
│── data.json         # track metadata storage
│── main.py           # entry point script
│── utils.py          # helpers (json parsing, tagging, etc.)
│── README.md         # this file
```

---

## ⚙️ Requirements

### 1. Install Dependencies
```bash
pip install yt-dlp mutagen requests
```

### 2. Install FFmpeg (required for yt-dlp audio conversion)
- **Ubuntu/Debian**  
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```  
- **macOS (brew)**  
  ```bash
  brew install ffmpeg
  ```  
- **Windows**  
  - Download from [ffmpeg.org](https://ffmpeg.org/download.html)  
  - Add `ffmpeg.exe` and `ffprobe.exe` to your PATH  

### 3. Install a Local LLM (for metadata cleaning)
We recommend [Ollama](https://ollama.ai/) with a lightweight LLaMA model.

Install Ollama:  
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Run a model (e.g. `llama3`):  
```bash
ollama run llama3
```

Your script will send the raw YouTube title → model → cleaned JSON metadata:  
```json
{"song":"Never Enough","artists":["Post Malone"]}
```

---

## 🚀 Usage

### Run the script directly
```bash
python main.py "https://www.youtube.com/watch?v=xxxx" "./covers/cover.jpg"
```

- Downloads YouTube video as high-quality MP3  
- Extracts captions → converts to SYLT → embeds as lyrics  
- Cleans metadata (song, artists) with LLM  
- Adds cover image from provided path  
- Saves final MP3 in `finished/`  

---

## 📜 Example Workflow

### Input
```bash
python main.py   "https://www.youtube.com/watch?v=abc123"   "./covers/post_malone.jpg"
```

### Output
- ✅ MP3 saved as:  
  ```
  finished/Never Enough - Post Malone.mp3
  ```
- ✅ Metadata inside MP3:  
  - Song: `Never Enough`  
  - Artists: `Post Malone`  
  - Lyrics: time-synced captions  
  - Cover: `post_malone.jpg`  
- ✅ `data.json` updated:  
  ```json
  [
    {
      "id": "abc123",
      "yt_url": "https://www.youtube.com/watch?v=abc123",
      "cover_path": "./covers/post_malone.jpg",
      "status": "done",
      "song": "Never Enough",
      "artists": ["Post Malone"],
      "output_file": "finished/Never Enough - Post Malone.mp3"
    }
  ]
  ```

---

## 🛠️ Roadmap
- [ ] Add Telegram bot integration for remote usage  
- [ ] Option to auto-download cover art from YouTube thumbnails  
- [ ] Batch processing from playlist/JSON  
- [ ] Web UI for easier usage  
- [ ] Docker support  

---

## ⚠️ Disclaimer
This project is for **personal and educational use only**.  
Please respect copyright laws in your country. Do not use this tool to distribute copyrighted music.  
