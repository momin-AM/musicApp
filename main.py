import tkinter as tk
from tkinter import ttk, filedialog
import os
import threading
import time
from player_logic import Player
from utils import scan_folder, get_metadata, format_time, LyricsService

class MusicPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Linux Music Player (Stability Mode)")
        self.root.geometry("900x650")
        
        # Initialize Player & Services
        self.player = Player()
        self.lyrics_service = LyricsService()
        self.playlist = []
        self.current_index = -1
        self.current_lyrics = []
        self.active_lyric_index = -1

        self.setup_styles()
        self.setup_ui()
        
        # Initial View
        self.show_library()
        
        # Start UI loop
        self.update_ui_cycle()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam') # Use clam for better Linux compatibility
        
        # Darkish theme colors
        bg_color = "#2e2e2e"
        fg_color = "#ffffff"
        
        self.root.configure(bg=bg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TButton", padding=5)
        style.configure("Vertical.TScrollbar", background=bg_color)

    def setup_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, width=150, bg="#1e1e1e")
        self.sidebar.pack(side="left", fill="y")
        
        tk.Label(self.sidebar, text="MusicApp", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=20)
        
        tk.Button(self.sidebar, text="Open Folder", command=self.load_folder).pack(fill="x", padx=10, pady=5)
        tk.Button(self.sidebar, text="Library", command=self.show_library).pack(fill="x", padx=10, pady=5)
        tk.Button(self.sidebar, text="Lyrics", command=self.show_lyrics).pack(fill="x", padx=10, pady=5)

        # Main Content area
        self.main_container = tk.Frame(self.root, bg="#2e2e2e")
        self.main_container.pack(side="top", fill="both", expand=True)

        # Library View (Listbox)
        self.library_frame = tk.Frame(self.main_container, bg="#2e2e2e")
        self.lib_scrollbar = tk.Scrollbar(self.library_frame)
        self.lib_scrollbar.pack(side="right", fill="y")
        
        self.playlist_box = tk.Listbox(self.library_frame, bg="#252525", fg="white", 
                                       selectbackground="#4a90e2", borderwidth=0, font=("Arial", 11))
        self.playlist_box.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.playlist_box.config(yscrollcommand=self.lib_scrollbar.set)
        self.lib_scrollbar.config(command=self.playlist_box.yview)
        self.playlist_box.bind('<Double-1>', lambda e: self.play_track(self.playlist_box.curselection()[0]))

        # Lyrics View (Text box)
        self.lyrics_frame = tk.Frame(self.main_container, bg="#2e2e2e")
        self.lyrics_text = tk.Text(self.lyrics_frame, bg="#252525", fg="gray", 
                                   font=("Arial", 14), wrap="word", borderwidth=0, padx=20, pady=20)
        self.lyrics_text.pack(fill="both", expand=True)
        self.lyrics_text.config(state="disabled")

        # Bottom Player Bar
        self.player_bar = tk.Frame(self.root, height=100, bg="#1e1e1e")
        self.player_bar.pack(side="bottom", fill="x")

        # Info
        self.info_label = tk.Label(self.player_bar, text="No track selected", bg="#1e1e1e", fg="white", font=("Arial", 10, "bold"))
        self.info_label.pack(side="left", padx=20)

        # Controls
        self.controls = tk.Frame(self.player_bar, bg="#1e1e1e")
        self.controls.pack(side="left", expand=True)

        tk.Button(self.controls, text="⏮", command=self.prev_track).pack(side="left", padx=5)
        self.play_btn = tk.Button(self.controls, text="▶", width=5, command=self.toggle_play)
        self.play_btn.pack(side="left", padx=5)
        tk.Button(self.controls, text="⏭", command=self.next_track).pack(side="left", padx=5)

        # Progress
        self.progress = tk.Scale(self.player_bar, from_=0, to=100, orient="horizontal", 
                                 showvalue=0, bg="#1e1e1e", highlightthickness=0)
        self.progress.pack(side="left", fill="x", expand=True, padx=20)

    def show_library(self):
        self.lyrics_frame.pack_forget()
        self.library_frame.pack(fill="both", expand=True)

    def show_lyrics(self):
        self.library_frame.pack_forget()
        self.lyrics_frame.pack(fill="both", expand=True)

    def load_folder(self):
        path = filedialog.askdirectory()
        if path:
            files = scan_folder(path)
            self.playlist = [get_metadata(f) for f in files]
            self.playlist_box.delete(0, tk.END)
            for track in self.playlist:
                self.playlist_box.insert(tk.END, f"{track['title']} - {track['artist']}")

    def play_track(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            track = self.playlist[index]
            if self.player.load(track['path']):
                self.player.play()
                self.info_label.config(text=f"{track['title']}\n{track['artist']}")
                self.play_btn.config(text="⏸")
                self.progress.config(to=track['duration'])
                threading.Thread(target=self.bg_load_lyrics, args=(track,), daemon=True).start()

    def bg_load_lyrics(self, track):
        lrc_text = self.lyrics_service.fetch_lyrics(track['title'], track['artist'], track['album'], track['duration'])
        self.current_lyrics = self.lyrics_service.parse_lrc(lrc_text)
        self.root.after(0, self.update_lyrics_ui)

    def update_lyrics_ui(self):
        self.lyrics_text.config(state="normal")
        self.lyrics_text.delete("1.0", tk.END)
        if not self.current_lyrics:
            self.lyrics_text.insert(tk.END, "\n\nLyrics not found", "center")
        else:
            for ts, text in self.current_lyrics:
                self.lyrics_text.insert(tk.END, text + "\n")
        self.lyrics_text.config(state="disabled")
        self.active_lyric_index = -1

    def toggle_play(self):
        if self.current_index == -1 and self.playlist: self.play_track(0)
        else:
            self.player.pause()
            self.root.after(50, self.update_play_button)

    def update_play_button(self):
        self.play_btn.config(text="⏸" if self.player.is_playing() else "▶")

    def next_track(self):
        if self.playlist: self.play_track((self.current_index + 1) % len(self.playlist))

    def prev_track(self):
        if self.playlist: self.play_track((self.current_index - 1) % len(self.playlist))

    def update_ui_cycle(self):
        if self.player.is_playing() or self.player.paused:
            pos = self.player.get_pos()
            self.progress.set(pos)
            self.sync_lyrics(pos)
        self.root.after(200, self.update_ui_cycle)

    def sync_lyrics(self, pos):
        if not self.current_lyrics: return
        idx = -1
        for i, (ts, text) in enumerate(self.current_lyrics):
            if pos >= ts: idx = i
            else: break
        
        if idx != self.active_lyric_index and idx != -1:
            self.lyrics_text.config(state="normal")
            # Dim all
            self.lyrics_text.tag_remove("active", "1.0", tk.END)
            self.lyrics_text.tag_add("inactive", "1.0", tk.END)
            self.lyrics_text.tag_config("inactive", foreground="gray")
            
            # Highlight active
            start_line = f"{idx + 1}.0"
            end_line = f"{idx + 1}.end"
            self.lyrics_text.tag_add("active", start_line, end_line)
            self.lyrics_text.tag_config("active", foreground="white", font=("Arial", 16, "bold"))
            
            # Scroll to active
            self.lyrics_text.see(start_line)
            self.lyrics_text.config(state="disabled")
            self.active_lyric_index = idx

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.mainloop()
