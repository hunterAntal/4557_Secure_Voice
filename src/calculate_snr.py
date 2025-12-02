"""
SNR Calculator for WAV Files
Compares two WAV files and calculates the Signal-to-Noise Ratio
"""

import argparse
import numpy as np
import wave
import sys
from pathlib import Path


def load_wav_file(filename: str) -> tuple:
    """
    Load a WAV file and return audio data and parameters

    Args:
        filename: Path to WAV file

    Returns:
        Tuple of (audio_data, sample_rate, duration)
    """
    try:
        with wave.open(filename, 'rb') as wav_file:
            # Get audio parameters
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()

            # Read audio data
            audio_data = wav_file.readframes(n_frames)

            # Convert to numpy array
            if sample_width == 2:  # 16-bit
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
            elif sample_width == 1:  # 8-bit
                audio_array = np.frombuffer(audio_data, dtype=np.uint8).astype(np.int16)
                audio_array = (audio_array - 128) * 256
            else:
                raise ValueError(f"Unsupported sample width: {sample_width} bytes")

            # Convert to mono if stereo
            if n_channels == 2:
                audio_array = audio_array.reshape(-1, 2).mean(axis=1)

            # Normalize to [-1.0, 1.0]
            if sample_width == 2:
                normalized = audio_array.astype(np.float64) / 32768.0
            else:
                normalized = audio_array.astype(np.float64) / 32768.0

            duration = n_frames / framerate

            return normalized, framerate, duration

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except wave.Error as e:
        print(f"Error: Invalid WAV file '{filename}': {e}")
        sys.exit(1)


def calculate_snr(original: np.ndarray, degraded: np.ndarray) -> dict:
    """
    Calculate Signal-to-Noise Ratio between two signals

    Args:
        original: Original (reference) signal
        degraded: Degraded (processed) signal

    Returns:
        Dictionary with SNR metrics
    """
    # Ensure same length
    min_len = min(len(original), len(degraded))
    if len(original) != len(degraded):
        print(f"Warning: Files have different lengths ({len(original)} vs {len(degraded)} samples)")
        print(f"         Using first {min_len} samples for comparison")

    original = original[:min_len]
    degraded = degraded[:min_len]

    # Calculate noise (error)
    noise = original - degraded

    # Calculate power
    signal_power = np.mean(original ** 2)
    noise_power = np.mean(noise ** 2)

    # Avoid division by zero
    if noise_power < 1e-10:
        snr_db = 100.0  # Very high SNR (essentially perfect)
    else:
        snr_db = 10 * np.log10(signal_power / noise_power)

    # Calculate additional metrics
    rms_signal = np.sqrt(signal_power)
    rms_noise = np.sqrt(noise_power)
    max_error = np.max(np.abs(noise))

    # Peak SNR (PSNR) - useful for digital signals
    peak_signal = np.max(np.abs(original))
    if noise_power > 0:
        psnr_db = 10 * np.log10((peak_signal ** 2) / noise_power)
    else:
        psnr_db = 100.0

    # Correlation coefficient
    correlation = np.corrcoef(original, degraded)[0, 1]

    return {
        'snr_db': snr_db,
        'psnr_db': psnr_db,
        'signal_power': signal_power,
        'noise_power': noise_power,
        'rms_signal': rms_signal,
        'rms_noise': rms_noise,
        'max_error': max_error,
        'correlation': correlation,
        'samples_compared': min_len
    }


def print_results(file1: str, file2: str, metrics: dict, sample_rate: float, duration: float):
    """Print SNR calculation results"""

    print("\n" + "=" * 70)
    print(" SNR CALCULATION RESULTS")
    print("=" * 70)

    print(f"\nOriginal file:  {file1}")
    print(f"Degraded file:  {file2}")
    print(f"Sample rate:    {sample_rate:.0f} Hz")
    print(f"Duration:       {duration:.3f} seconds")
    print(f"Samples:        {metrics['samples_compared']:,}")

    print("\n" + "-" * 70)
    print(" SIGNAL-TO-NOISE RATIO")
    print("-" * 70)

    print(f"\nSNR:            {metrics['snr_db']:.2f} dB")
    print(f"PSNR:           {metrics['psnr_db']:.2f} dB (Peak SNR)")

    # Interpretation
    print(f"\nInterpretation:")
    if metrics['snr_db'] >= 60:
        print(f"  Excellent quality (SNR ≥ 60 dB)")
    elif metrics['snr_db'] >= 40:
        print(f"  Very good quality (40-60 dB)")
    elif metrics['snr_db'] >= 30:
        print(f"  Good quality (30-40 dB)")
    elif metrics['snr_db'] >= 20:
        print(f"  Fair quality (20-30 dB)")
    else:
        print(f"  Poor quality (SNR < 20 dB)")

    print("\n" + "-" * 70)
    print(" DETAILED METRICS")
    print("-" * 70)

    print(f"\nSignal Power:   {metrics['signal_power']:.6f}")
    print(f"Noise Power:    {metrics['noise_power']:.6f}")
    print(f"RMS Signal:     {metrics['rms_signal']:.6f}")
    print(f"RMS Noise:      {metrics['rms_noise']:.6f}")
    print(f"Max Error:      {metrics['max_error']:.6f}")
    print(f"Correlation:    {metrics['correlation']:.6f}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Calculate SNR between two WAV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare original and received audio
  python calculate_snr.py original.wav received.wav

  # Compare with output file
  python calculate_snr.py original.wav processed.wav --output snr_results.txt

SNR Interpretation:
  > 60 dB  - Excellent (virtually identical)
  40-60 dB - Very good (high quality audio)
  30-40 dB - Good (acceptable for most uses)
  20-30 dB - Fair (noticeable degradation)
  < 20 dB  - Poor (significant degradation)
        """
    )

    parser.add_argument('original', type=str,
                        help='Original (reference) WAV file')
    parser.add_argument('degraded', type=str,
                        help='Degraded (processed) WAV file to compare')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Save results to text file')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Only print SNR value')

    args = parser.parse_args()

    # Validate files exist
    if not Path(args.original).exists():
        print(f"Error: Original file '{args.original}' not found")
        sys.exit(1)

    if not Path(args.degraded).exists():
        print(f"Error: Degraded file '{args.degraded}' not found")
        sys.exit(1)

    # Load audio files
    if not args.quiet:
        print("Loading audio files...")

    original_audio, orig_rate, orig_duration = load_wav_file(args.original)
    degraded_audio, deg_rate, deg_duration = load_wav_file(args.degraded)

    # Check sample rates match
    if orig_rate != deg_rate:
        print(f"Warning: Sample rates differ ({orig_rate} Hz vs {deg_rate} Hz)")
        print(f"         Resampling may be needed for accurate comparison")

    # Calculate SNR
    metrics = calculate_snr(original_audio, degraded_audio)

    # Print results
    if args.quiet:
        print(f"{metrics['snr_db']:.2f}")
    else:
        print_results(args.original, args.degraded, metrics, orig_rate, orig_duration)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write(" SNR CALCULATION RESULTS\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Original file:  {args.original}\n")
            f.write(f"Degraded file:  {args.degraded}\n")
            f.write(f"Sample rate:    {orig_rate:.0f} Hz\n")
            f.write(f"Duration:       {orig_duration:.3f} seconds\n")
            f.write(f"Samples:        {metrics['samples_compared']:,}\n\n")
            f.write("-" * 70 + "\n")
            f.write(" SIGNAL-TO-NOISE RATIO\n")
            f.write("-" * 70 + "\n\n")
            f.write(f"SNR:            {metrics['snr_db']:.2f} dB\n")
            f.write(f"PSNR:           {metrics['psnr_db']:.2f} dB\n\n")
            f.write("-" * 70 + "\n")
            f.write(" DETAILED METRICS\n")
            f.write("-" * 70 + "\n\n")
            f.write(f"Signal Power:   {metrics['signal_power']:.6f}\n")
            f.write(f"Noise Power:    {metrics['noise_power']:.6f}\n")
            f.write(f"RMS Signal:     {metrics['rms_signal']:.6f}\n")
            f.write(f"RMS Noise:      {metrics['rms_noise']:.6f}\n")
            f.write(f"Max Error:      {metrics['max_error']:.6f}\n")
            f.write(f"Correlation:    {metrics['correlation']:.6f}\n")
            f.write("=" * 70 + "\n")

        if not args.quiet:
            print(f"\nResults saved to: {args.output}")

    # Exit code based on SNR quality
    if metrics['snr_db'] >= 40:
        sys.exit(0)  # Good quality
    elif metrics['snr_db'] >= 30:
        sys.exit(1)  # Acceptable quality
    else:
        sys.exit(2)  # Poor quality


if __name__ == "__main__":
    main()
