import socket
import numpy as np
import time
from faster_whisper import WhisperModel
from silero_vad import VADIterator, load_silero_vad

# --- Configuration ---
UDP_IP = "0.0.0.0"
UDP_PORT = 5004
RTP_HEADER_SIZE = 12
SAMPLE_RATE = 16000
VAD_CHUNK_SIZE = 512  # Silero requires exactly 512 samples for 16kHz

def main():
    print("🚀 Loading Silero VAD (ONNX) & Faster-Whisper...")
    # Load ONNX version to avoid the Python 3.13 / Torchaudio crash
    model_vad = load_silero_vad(onnx=True) 
    vad_iterator = VADIterator(model_vad, threshold=0.5, min_silence_duration_ms=700)

    # i5-9400 optimized Whisper
    stt_model = WhisperModel("tiny.en", device="cpu", compute_type="int8", cpu_threads=6)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    accumulated_samples = np.array([], dtype=np.float32)
    sentence_audio = []
    is_collecting = False

    print("✅ Ready! Listening for speech...")

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if len(data) <= RTP_HEADER_SIZE: continue

            # 1. Convert incoming UDP packet to float32
            pcm_payload = data[RTP_HEADER_SIZE:]
            new_samples = np.frombuffer(pcm_payload, dtype='>i2').astype(np.float32) / 32768.0
            
            # 2. Add to our VAD buffer
            accumulated_samples = np.append(accumulated_samples, new_samples)

            # 3. Process in blocks of exactly 512 samples
            while len(accumulated_samples) >= VAD_CHUNK_SIZE:
                vad_block = accumulated_samples[:VAD_CHUNK_SIZE]
                accumulated_samples = accumulated_samples[VAD_CHUNK_SIZE:]

                # Feed the exact 512-sample block to VAD
                speech_dict = vad_iterator(vad_block, return_seconds=False)

                if speech_dict:
                    if "start" in speech_dict:
                        is_collecting = True
                        sentence_audio = [vad_block]
                        print("🎤 Speech detected...", end="\r")
                    
                    if "end" in speech_dict:
                        if is_collecting and sentence_audio:
                            print("\n⚙️  Processing sentence...")
                            full_audio = np.concatenate(sentence_audio)
                            
                            # --- Latency Debugging Start ---
                            start_time = time.perf_counter()
                            
                            segments, _ = stt_model.transcribe(full_audio, beam_size=1)
                            text = "".join([s.text for s in segments]).strip()
                            
                            end_time = time.perf_counter()
                            latency = (end_time - start_time) * 1000 # Convert to ms
                            # --- Latency Debugging End ---
                            
                            if text:
                                # Printing latency for debugging
                                print(f"🗣️  {text} [Inference: {latency:.2f}ms]")
                                
                                
                            
                            is_collecting = False
                            sentence_audio = []
                
                # If we are in the middle of a sentence, keep the audio
                if is_collecting:
                    sentence_audio.append(vad_block)

        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()
    
    
"""import socket
import numpy as np
import time
import os
from faster_whisper import WhisperModel
from silero_vad import VADIterator, load_silero_vad

# --- Configuration ---
UDP_IP = "0.0.0.0"
UDP_PORT = 5004
RTP_HEADER_SIZE = 12
SAMPLE_RATE = 16000
VAD_CHUNK_SIZE = 512  # Silero requires exactly 512 samples for 16kHz

def main():
    print("🚀 Loading Silero VAD (ONNX) & Faster-Whisper...")
    # Load ONNX version to avoid the Python 3.13 / Torchaudio crash
    model_vad = load_silero_vad(onnx=True) 
    vad_iterator = VADIterator(model_vad, threshold=0.5, min_silence_duration_ms=700)

    # Path to your local 'small' model folder
    model_path = "./small"
    
    if not os.path.exists(model_path):
        print(f"⚠️ Warning: Local folder '{model_path}' not found. Downloading 'small' instead.")
        model_to_load = "small"
    else:
        print(f"📂 Using local model from: {model_path}")
        model_to_load = model_path

    # i5-9400 optimized Whisper using the 'small' model
    # compute_type="int8" is critical here to fit in 8GB RAM
    stt_model = WhisperModel(
        model_to_load, 
        device="cpu", 
        compute_type="int8", 
        cpu_threads=6,
        num_workers=1
    )
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    accumulated_samples = np.array([], dtype=np.float32)
    sentence_audio = []
    is_collecting = False

    print("✅ Ready! Listening for speech...")

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if len(data) <= RTP_HEADER_SIZE: continue

            # 1. Convert incoming UDP packet to float32
            pcm_payload = data[RTP_HEADER_SIZE:]
            new_samples = np.frombuffer(pcm_payload, dtype='>i2').astype(np.float32) / 32768.0
            
            # 2. Add to our VAD buffer
            accumulated_samples = np.append(accumulated_samples, new_samples)

            # 3. Process in blocks of exactly 512 samples
            while len(accumulated_samples) >= VAD_CHUNK_SIZE:
                vad_block = accumulated_samples[:VAD_CHUNK_SIZE]
                accumulated_samples = accumulated_samples[VAD_CHUNK_SIZE:]

                # Feed the exact 512-sample block to VAD
                speech_dict = vad_iterator(vad_block, return_seconds=False)

                if speech_dict:
                    if "start" in speech_dict:
                        is_collecting = True
                        sentence_audio = [vad_block]
                        print("🎤 Speech detected...", end="\r")
                    
                    if "end" in speech_dict:
                        if is_collecting and sentence_audio:
                            print("\n⚙️  Processing sentence...")
                            full_audio = np.concatenate(sentence_audio)
                            
                            # --- Latency Debugging Start ---
                            start_time = time.perf_counter()
                            
                            segments, _ = stt_model.transcribe(full_audio, beam_size=1)
                            text = "".join([s.text for s in segments]).strip()
                            
                            end_time = time.perf_counter()
                            latency = (end_time - start_time) * 1000 # Convert to ms
                            # --- Latency Debugging End ---
                            
                            if text:
                                # Printing latency for debugging
                                print(f"🗣️  {text} [Inference: {latency:.2f}ms]")
                            
                            is_collecting = False
                            sentence_audio = []
                
                # If we are in the middle of a sentence, keep the audio
                if is_collecting:
                    sentence_audio.append(vad_block)

        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()"""
    
    