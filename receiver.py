"""
Secure Voice Receiver
Receives and decrypts audio for playback
"""

import argparse
import socket
import time
import numpy as np
import wave
from audio_processor import AudioProcessor
from secure_channel import SecureChannel
from crypto_module import CryptoModule


class VoiceReceiver:
    """
    Receiver for secure voice communication
    """

    def __init__(self, port: int, private_key: bytes, public_key: bytes):
        """
        Initialize receiver

        Args:
            port: Port to listen on
            private_key: RSA private key (PEM)
            public_key: RSA public key (PEM)
        """
        self.port = port

        # Initialize components
        self.audio_processor = AudioProcessor(sample_rate=8000, bits=16)
        self.channel = SecureChannel(private_key, public_key)

        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))

        # Storage for received audio
        self.received_audio = []



    def receive_audio(self, max_duration: float = 60.0):
        """
        Receive audio data

        Args:
            max_duration: Maximum reception time (seconds)
        """
        print(f"Listening on port {self.port}...")

        # Wait for and establish secure connection
        print("\nWaiting for secure handshake...")
        if not self.channel.handshake_responder(self.socket):
            print("Failed to establish secure connection")
            return

        print("\nReceiving audio data...")
        print("Press Ctrl+C to stop\n")

        start_time = time.time()
        last_packet_time = time.time()
        packet_count = 0
        timeout_threshold = 2.0  # Consider session ended after 2s silence

        try:
            while True:
                elapsed = time.time() - start_time

                # Check timeout
                if elapsed > max_duration:
                    print(f"\nMaximum duration ({max_duration}s) reached")
                    break

                # Check if session ended (no packets for a while)
                if time.time() - last_packet_time > timeout_threshold and packet_count > 0:
                    print(f"\nNo packets received for {timeout_threshold}s - session ended")
                    break

                # Receive packet
                data = self.channel.receive_data(timeout=0.5)

                if data is not None:
                    last_packet_time = time.time()
                    packet_count += 1

                    # Reconstruct audio from compressed data
                    # Data format: compressed ADPCM audio + metadata
                    # For simplicity, assume data is the compressed audio
                    reconstructed = self.audio_processor.process_for_playback(data, len(data) * 4)

                    self.received_audio.append(reconstructed)

                    # Progress indicator
                    if packet_count % 10 == 0:
                        duration = len(np.concatenate(self.received_audio)) / self.audio_processor.sample_rate
                        print(f"  Received {packet_count} packets ({duration:.1f}s audio)")

        except KeyboardInterrupt:
            print("\nReception stopped by user")

        elapsed = time.time() - start_time

        # Compile statistics
        stats = self.channel.get_statistics()

        print(f"\nReception complete!")
        print(f"  Total time: {elapsed:.2f} seconds")
        print(f"  Packets received: {stats['packets_received']}")
        print(f"  Errors corrected: {stats['errors_corrected']}")

        # Close session
        self.channel.close()

    def save_audio(self, filename: str):
        """
        Save received audio to WAV file

        Args:
            filename: Output filename
        """
        if not self.received_audio:
            print("No audio data to save")
            return

        # Concatenate all chunks
        audio_data = np.concatenate(self.received_audio)

        # Convert to 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)

        print(f"\nSaving audio to {filename}...")
        print(f"  Samples: {len(audio_int16)}")
        print(f"  Duration: {len(audio_int16) / self.audio_processor.sample_rate:.2f} seconds")

        # Write WAV file
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.audio_processor.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        print(f"✓ Audio saved successfully")

    def calculate_metrics(self, original_audio: np.ndarray = None):
        """
        Calculate quality metrics

        Args:
            original_audio: Original audio for comparison (if available)
        """
        if not self.received_audio:
            print("No audio data received")
            return

        audio_data = np.concatenate(self.received_audio)

        print("\n" + "=" * 60)
        print("AUDIO QUALITY METRICS")
        print("=" * 60)

        # Basic metrics
        print(f"\nReceived Audio:")
        print(f"  Samples: {len(audio_data)}")
        print(f"  Duration: {len(audio_data) / self.audio_processor.sample_rate:.2f} seconds")
        print(f"  Sample rate: {self.audio_processor.sample_rate} Hz")
        print(f"  Peak amplitude: {np.max(np.abs(audio_data)):.3f}")
        print(f"  RMS level: {np.sqrt(np.mean(audio_data ** 2)):.3f}")

        # SNR calculation (if original provided)
        if original_audio is not None:
            # Align lengths
            min_len = min(len(audio_data), len(original_audio))
            audio_data_trim = audio_data[:min_len]
            original_trim = original_audio[:min_len]

            snr = self.audio_processor.calculate_snr(original_trim, audio_data_trim)
            print(f"\nSignal-to-Noise Ratio:")
            print(f"  SNR: {snr:.2f} dB")
            print(f"  Requirement: ≤ 40 dB")
            print(f"  Status: {'✓ PASS' if snr <= 40 else '✗ FAIL'}")

        # Transmission efficiency
        stats = self.channel.get_statistics()
        if stats['packets_received'] > 0:
            avg_packet_size = len(audio_data) * 2 / stats['packets_received']  # bytes
            bitrate = (avg_packet_size * 8 * stats['packets_received']) / (len(audio_data) / self.audio_processor.sample_rate) / 1000

            print(f"\nTransmission Statistics:")
            print(f"  Average packet size: {avg_packet_size:.1f} bytes")
            print(f"  Effective bitrate: {bitrate:.1f} Kbps")
            print(f"  Requirement: >= 64 Kbps")
            print(f"  Status: {'✓ PASS' if bitrate >= 64 else '✗ FAIL'}")


def generate_keys():
    """Generate RSA key pair for testing"""
    crypto = CryptoModule()
    private_key, public_key = crypto.generate_rsa_keypair()

    # Save keys
    with open('receiver_private.pem', 'wb') as f:
        f.write(private_key)

    with open('receiver_public.pem', 'wb') as f:
        f.write(public_key)

    print("Generated receiver keys:")
    print("  receiver_private.pem")
    print("  receiver_public.pem")

    return private_key, public_key

def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't actually need to reach Google — just selects the right interface
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip


def main():
    parser = argparse.ArgumentParser(description='Secure Voice Receiver')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to listen on')
    parser.add_argument('--output', type=str, default='received_audio.wav',
                        help='Output audio file')
    parser.add_argument('--max-duration', type=float, default=60.0,
                        help='Maximum reception time (seconds)')
    parser.add_argument('--generate-keys', action='store_true',
                        help='Generate new RSA keys')

    args = parser.parse_args()

    # Generate keys if requested
    if args.generate_keys:
        generate_keys()
        return

    # Load or generate keys
    try:
        with open('receiver_private.pem', 'rb') as f:
            private_key = f.read()
        with open('receiver_public.pem', 'rb') as f:
            public_key = f.read()
        print("Loaded existing keys")
    except FileNotFoundError:
        print("No keys found, generating new keys...")
        private_key, public_key = generate_keys()

    # Create receiver
    print(f"\nInitializing receiver...")
    print(f"Port: {args.port}")

    receiver_ip = get_local_ip()
    print(f"Receiver IP Address: {receiver_ip}")

    receiver = VoiceReceiver(args.port, private_key, public_key)

    # Receive audio
    try:
        receiver.receive_audio(max_duration=args.max_duration)
    except Exception as e:
        print(f"Reception error: {e}")
        import traceback
        traceback.print_exc()

    # Save received audio
    if receiver.received_audio:
        receiver.save_audio(args.output)
        receiver.calculate_metrics()


if __name__ == "__main__":
    main()
