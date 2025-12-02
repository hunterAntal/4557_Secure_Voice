"""
Audio Resampler
Resamples WAV files to a target sample rate (default 8000 Hz for voice transmission)
"""

import argparse
import wave
import numpy as np
from scipy import signal as sp_signal
import sys


def resample_audio(input_file: str, output_file: str, target_rate: int = 8000):
    """
    Resample a WAV file to a target sample rate

    Args:
        input_file: Input WAV file path
        output_file: Output WAV file path
        target_rate: Target sample rate in Hz (default 8000)
    """
    print(f"Resampling {input_file}...")

    # Read input file
    with wave.open(input_file, 'rb') as wav_in:
        # Get parameters
        n_channels = wav_in.getnchannels()
        sample_width = wav_in.getsampwidth()
        orig_rate = wav_in.getframerate()
        n_frames = wav_in.getnframes()

        print(f"  Original sample rate: {orig_rate} Hz")
        print(f"  Target sample rate:   {target_rate} Hz")
        print(f"  Channels:             {n_channels}")
        print(f"  Sample width:         {sample_width} bytes")
        print(f"  Duration:             {n_frames / orig_rate:.2f} seconds")

        # Read audio data
        audio_data = wav_in.readframes(n_frames)

        # Convert to numpy array
        if sample_width == 2:  # 16-bit
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
        elif sample_width == 1:  # 8-bit
            audio_array = np.frombuffer(audio_data, dtype=np.uint8).astype(np.int16)
            audio_array = (audio_array - 128) * 256
        else:
            raise ValueError(f"Unsupported sample width: {sample_width} bytes")

    # Handle stereo
    if n_channels == 2:
        print("  Converting stereo to mono...")
        audio_array = audio_array.reshape(-1, 2).mean(axis=1).astype(np.int16)
        n_channels = 1

    # Resample if needed
    if orig_rate != target_rate:
        print(f"  Resampling from {orig_rate} Hz to {target_rate} Hz...")

        # Calculate new length
        num_samples = int(len(audio_array) * target_rate / orig_rate)

        # Use scipy's high-quality resampler
        resampled = sp_signal.resample(audio_array, num_samples)

        # Convert back to int16
        resampled = np.clip(resampled, -32768, 32767).astype(np.int16)
    else:
        print("  Sample rate already matches target")
        resampled = audio_array

    # Write output file
    print(f"  Writing {output_file}...")
    with wave.open(output_file, 'wb') as wav_out:
        wav_out.setnchannels(n_channels)
        wav_out.setsampwidth(2)  # Always output 16-bit
        wav_out.setframerate(target_rate)
        wav_out.writeframes(resampled.tobytes())

    new_duration = len(resampled) / target_rate
    print(f"\n✓ Resampling complete!")
    print(f"  Output samples:  {len(resampled):,}")
    print(f"  Output duration: {new_duration:.2f} seconds")
    print(f"  Output size:     {len(resampled) * 2:,} bytes")


def main():
    parser = argparse.ArgumentParser(
        description='Resample WAV files for voice transmission',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resample to 8000 Hz (default for voice transmission)
  python resample_audio.py audio.wav audio_8k.wav

  # Resample to custom rate
  python resample_audio.py audio.wav audio_16k.wav --rate 16000

  # Batch resample multiple files
  for file in *.wav; do
    python resample_audio.py "$file" "resampled_$file"
  done
        """
    )

    parser.add_argument('input', type=str,
                        help='Input WAV file')
    parser.add_argument('output', type=str,
                        help='Output WAV file')
    parser.add_argument('--rate', '-r', type=int, default=8000,
                        help='Target sample rate in Hz (default: 8000)')

    args = parser.parse_args()

    try:
        resample_audio(args.input, args.output, args.rate)
    except FileNotFoundError:
        print(f"Error: File '{args.input}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
