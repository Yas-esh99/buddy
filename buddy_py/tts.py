import queue
import threading
import time

import numpy as np
import sounddevice as sd
from piper import PiperVoice


class PiperTTSManager:
    """
    Background TTS worker for Piper.
    - Keeps full text intact for natural speech
    - Plays audio in a separate thread
    - Can interrupt current speech
    - Queues multiple speak requests
    """

    def __init__(self, model_path: str, use_cuda: bool = False):
        self.voice = PiperVoice.load(model_path, use_cuda=use_cuda)
        self.jobs = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.current_stream = None
        self.worker.start()

    def speak(self, text: str):
        """Queue text to be spoken."""
        if not text or not text.strip():
            return
        self.jobs.put(text.strip())

    def stop(self):
        """Stop current speech and clear queued speech."""
        self.stop_event.set()

        # Clear pending jobs
        try:
            while True:
                self.jobs.get_nowait()
        except queue.Empty:
            pass

        # Stop active audio stream immediately if open
        if self.current_stream is not None:
            try:
                self.current_stream.abort()
            except Exception:
                pass
            try:
                self.current_stream.close()
            except Exception:
                pass
            self.current_stream = None

    def wait_until_idle(self):
        """Block until queue is empty and current speech is done."""
        while not self.jobs.empty() or self.current_stream is not None:
            time.sleep(0.05)

    def _worker_loop(self):
        while True:
            text = self.jobs.get()
            self.stop_event.clear()
            try:
                self._speak_text(text)
            except Exception as e:
                print(f"[TTS error] {e}")
            finally:
                self.current_stream = None
                self.stop_event.clear()

    def _speak_text(self, text: str):
        """
        Stream audio from Piper and play it immediately.

        Important:
        - Piper sees the full sentence
        - We only chunk the generated audio for playback
        """
        stream = None

        for chunk in self.voice.synthesize(text):
            if self.stop_event.is_set():
                break

            # First chunk tells us the audio format
            if stream is None:
                sample_rate = chunk.sample_rate
                channels = chunk.sample_channels

                try:
                    stream = sd.RawOutputStream(
                        samplerate=sample_rate,
                        channels=channels,
                        dtype="int16",
                        blocksize=0,
                    )
                    stream.start()
                    self.current_stream = stream
                except Exception as stream_err:
                    print(f"[Stream Error] {stream_err}")
                    return

            # Stream raw PCM bytes
            audio_bytes = chunk.audio_int16_bytes

            if self.stop_event.is_set():
                break

            try:
                stream.write(audio_bytes)
            except Exception as write_err:
                print(f"[Write Error] {write_err}")
                break

        if stream is not None:
            try:
                stream.stop()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass

        self.current_stream = None


if __name__ == "__main__":
    # Change this to your downloaded voice model path
    # Example voice download:
    #   python3 -m piper.download_voices en_US-lessac-medium
    #
    # Then point to the downloaded .onnx file.
    MODEL_PATH = "models/en_US-danny-low.onnx"

    tts = PiperTTSManager(MODEL_PATH, use_cuda=False)

    # Speak in background while main processing continues
    tts.speak("Hello sir, I am ready.")
    print("Main processing continues here...")

    time.sleep(2)

    tts.speak("I can keep talking while your main logic runs.")

    time.sleep(1.5)

    # Interrupt current speech
    print("Stopping TTS now...")
    tts.stop()

    time.sleep(1)

    # Speak again
    tts.speak("This is a new message after interruption.")
    tts.wait_until_idle()