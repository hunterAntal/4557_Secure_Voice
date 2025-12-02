"""
Secure Voice Transmitter
Captures audio and transmits securely
"""

import argparse
import socket
import time
import numpy as np
import wave
from pathlib import Path
from audio_processor import AudioProcessor
from secure_channel import SecureChannel
from crypto_module import CryptoModule


class VoiceTransmitter:
    """
    Transmitter for secure voice communication
    """

    def __init__(self, host: str, port: int, private_key: bytes, public_key: bytes):
        """
        Initialize transmitter

        Args:
            host: Receiver host address
            port: Receiver port
            private_key: RSA private key (PEM)
            public_key: RSA public key (PEM)
        """
        self.host = host
        self.port = port

        # Initialize components
        self.audio_processor = AudioProcessor(sample_rate=8000, bits=16)
        self.channel = SecureChannel(private_key, public_key)

        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def load_audio_file(self, filename: str) -> np.ndarray:
        """
        Load audio from WAV file

        Args:
            filename: Path to WAV file

        Returns:
            Normalized audio data
        """
        print(f"Loading audio file: {filename}")

        with wave.open(filename, 'rb') as wav_file:
            # Get audio parameters
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()

            print(f"  Channels: {n_channels}")
            print(f"  Sample width: {sample_width} bytes")
            print(f"  Frame rate: {framerate} Hz")
            print(f"  Duration: {n_frames / framerate:.2f} seconds")

            # Read audio data
            audio_data = wav_file.readframes(n_frames)

            # Convert to numpy array
            if sample_width == 2:  # 16-bit
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
            elif sample_width == 1:  # 8-bit
                audio_array = np.frombuffer(audio_data, dtype=np.uint8).astype(np.int16)
                audio_array = (audio_array - 128) * 256
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")

            # Convert to mono if stereo
            if n_channels == 2:
                audio_array = audio_array.reshape(-1, 2).mean(axis=1).astype(np.int16)

            # Resample if needed
            if framerate != self.audio_processor.sample_rate:
                print(f"  Resampling from {framerate} Hz to {self.audio_processor.sample_rate} Hz")
                # Simple resampling
                ratio = self.audio_processor.sample_rate / framerate
                new_length = int(len(audio_array) * ratio)
                audio_array = np.interp(
                    np.linspace(0, len(audio_array), new_length),
                    np.arange(len(audio_array)),
                    audio_array
                ).astype(np.int16)

            # Normalize to [-1.0, 1.0]
            normalized = audio_array.astype(np.float32) / 32768.0

            return normalized

    def generate_test_tone(self, duration: float = 5.0, frequency: float = 1000.0) -> np.ndarray:
        """
        Generate test tone for demonstration

        Args:
            duration: Duration in seconds
            frequency: Tone frequency in Hz

        Returns:
            Normalized audio data
        """
        print(f"Generating {frequency} Hz test tone ({duration} seconds)")

        t = np.linspace(0, duration, int(self.audio_processor.sample_rate * duration))
        tone = 0.3 * np.sin(2 * np.pi * frequency * t)

        return tone

    def transmit_audio(self, audio_data: np.ndarray, chunk_size: int = 1600):
        """
        Transmit audio data securely

        Args:
            audio_data: Normalized audio samples
            chunk_size: Number of samples per packet (0.2 sec @ 8kHz)
        """
        print(f"\nTransmitting {len(audio_data)} samples...")
        print(f"Chunk size: {chunk_size} samples ({chunk_size / self.audio_processor.sample_rate:.3f} sec)")

        # Establish secure connection
        print("\nEstablishing secure connection...")
        if not self.channel.handshake_initiator(self.socket, (self.host, self.port)):
            print("Failed to establish secure connection")
            return

        # Transmit in chunks
        total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size
        start_time = time.time()

        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            chunk_num = i // chunk_size + 1

            # Process chunk for transmission
            compressed, num_samples = self.audio_processor.process_for_transmission(chunk)

            # Send securely
            if not self.channel.send_data(compressed):
                print(f"Failed to send chunk {chunk_num}")
                break

            # Progress indicator
            if chunk_num % 10 == 0 or chunk_num == total_chunks:
                elapsed = time.time() - start_time
                progress = chunk_num / total_chunks * 100
                print(f"  Progress: {chunk_num}/{total_chunks} chunks ({progress:.1f}%) "
                      f"- {elapsed:.1f}s elapsed")

            # Pace transmission (simulate real-time)
            time.sleep(chunk_size / self.audio_processor.sample_rate * 0.8)

        elapsed = time.time() - start_time
        print(f"\nTransmission complete!")
        print(f"  Total time: {elapsed:.2f} seconds")
        print(f"  Audio duration: {len(audio_data) / self.audio_processor.sample_rate:.2f} seconds")

        # Display statistics
        stats = self.channel.get_statistics()
        print(f"\nTransmission statistics:")
        print(f"  Packets sent: {stats['packets_sent']}")
        print(f"  Session active: {stats['session_active']}")

        # Close session
        self.channel.close()


def generate_keys():
    """Generate RSA key pair for testing"""
    crypto = CryptoModule()
    private_key, public_key = crypto.generate_rsa_keypair()

    # Save keys
    with open('transmitter_private.pem', 'wb') as f:
        f.write(private_key)

    with open('transmitter_public.pem', 'wb') as f:
        f.write(public_key)

    print("Generated transmitter keys:")
    print("  transmitter_private.pem")
    print("  transmitter_public.pem")

    return private_key, public_key


def main():
    parser = argparse.ArgumentParser(description='Secure Voice Transmitter')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Receiver host address')
    parser.add_argument('--port', type=int, default=5000,
                        help='Receiver port')
    parser.add_argument('--audio', type=str, default=None,
                        help='Audio file to transmit (WAV format)')
    parser.add_argument('--test-tone', action='store_true',
                        help='Generate and transmit test tone')
    parser.add_argument('--duration', type=float, default=5.0,
                        help='Test tone duration (seconds)')
    parser.add_argument('--generate-keys', action='store_true',
                        help='Generate new RSA keys')

    args = parser.parse_args()

    # Generate keys if requested
    if args.generate_keys:
        generate_keys()
        return

    # Load or generate keys
    try:
        with open('transmitter_private.pem', 'rb') as f:
            private_key = f.read()
        with open('transmitter_public.pem', 'rb') as f:
            public_key = f.read()
        print("Loaded existing keys")
    except FileNotFoundError:
        print("No keys found, generating new keys...")
        private_key, public_key = generate_keys()

    # Create transmitter
    print(f"\nInitializing transmitter...")
    print(f"Target: {args.host}:{args.port}")

    transmitter = VoiceTransmitter(args.host, args.port, private_key, public_key)

    # Load or generate audio
    if args.audio:
        audio_data = transmitter.load_audio_file(args.audio)
    else:
        audio_data = transmitter.generate_test_tone(duration=args.duration)

    # Transmit
    try:
        transmitter.transmit_audio(audio_data)
    except KeyboardInterrupt:
        print("\nTransmission interrupted")
    except Exception as e:
        print(f"Transmission error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
