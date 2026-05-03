import vlc
import os

class Player:
    def __init__(self):
        # Initialize VLC instance
        # --no-video to ensure it only handles audio
        self.instance = vlc.Instance('--no-video', '--quiet')
        self.mediaplayer = self.instance.media_player_new()
        
        self.current_track = None
        self.paused = False
        self.volume = 50  # VLC volume is 0-100
        self.mediaplayer.audio_set_volume(self.volume)

    def load(self, file_path):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        try:
            media = self.instance.media_new(file_path)
            self.mediaplayer.set_media(media)
            self.current_track = file_path
            self.paused = False
            return True
        except Exception as e:
            print(f"Error loading {file_path} with VLC: {e}")
            return False

    def play(self):
        if self.current_track:
            try:
                self.mediaplayer.play()
                self.paused = False
            except Exception as e:
                print(f"Play error: {e}")

    def pause(self):
        try:
            # VLC pause() toggles between pause and play
            self.mediaplayer.pause()
            # We need to manually track state as pause() is a toggle in some VLC versions
            # but usually it behaves correctly. We'll check the state.
            state = self.mediaplayer.get_state()
            self.paused = (state == vlc.State.Paused)
        except Exception as e:
            print(f"Pause error: {e}")

    def stop(self):
        try:
            self.mediaplayer.stop()
            self.paused = False
        except Exception as e:
            print(f"Stop error: {e}")

    def set_volume(self, volume):
        """volume: float from 0.0 to 1.0"""
        self.volume = int(volume * 100)
        try:
            self.mediaplayer.audio_set_volume(self.volume)
        except Exception as e:
            print(f"Volume error: {e}")

    def get_pos(self):
        """Returns current position in seconds."""
        try:
            # get_time() returns ms
            return self.mediaplayer.get_time() / 1000.0
        except:
            return 0

    def is_playing(self):
        try:
            state = self.mediaplayer.get_state()
            return state == vlc.State.Playing
        except:
            return False

    def quit(self):
        try:
            self.mediaplayer.release()
            self.instance.release()
        except:
            pass
