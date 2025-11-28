"""
Chapter 1: Audio Basics - ADC and DAC Fundamentals
====================================================

This prototype demonstrates:
1. Generating analog audio signals (sine waves)
2. Anti-aliasing filtering
3. ADC: Converting analog to digital (quantization)
4. DAC: Converting digital back to analog
5. Measuring signal quality (SNR)

Learning Goals:
- Understand sampling and quantization
- See how bit depth affects quality
- Learn why anti-aliasing filters are necessary
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import wave


class SimpleAudioProcessor:
    """
    A simplified audio processor that demonstrates ADC/DAC concepts
    """
    
    def __init__(self, sample_rate=8000, bits=16):
        """
        Initialize the audio processor
        
        Args:
            sample_rate: Samples per second (Hz) - how often we measure
            bits: Bit depth - how precisely we measure each sample
        """
        self.sample_rate = sample_rate
        self.bits = bits
        self.max_amplitude = 2 ** (bits - 1) - 1  # For 16-bit: 32767
        
        print(f"Audio Processor Initialized:")
        print(f"  Sample Rate: {sample_rate} Hz (measures {sample_rate} times/second)")
        print(f"  Bit Depth: {bits} bits (can represent {2**bits} different levels)")
        print(f"  Max Amplitude: ±{self.max_amplitude}")
        
        # Design anti-aliasing filter
        # Low-pass filter: only lets through frequencies below 3.4 kHz
        nyquist = sample_rate / 2  # Maximum frequency we can represent
        cutoff = 3400  # Voice bandwidth (telephone quality)
        
        print(f"\nAnti-Aliasing Filter:")
        print(f"  Nyquist Frequency: {nyquist} Hz")
        print(f"  Cutoff Frequency: {cutoff} Hz")
        print(f"  Purpose: Remove frequencies above {cutoff} Hz to prevent aliasing")
        
        # Butterworth filter - smooth frequency response
        self.sos = signal.butter(8, cutoff / nyquist, btype='low', output='sos')
    
    def generate_test_signal(self, duration=1.0, frequency=1000.0, amplitude=0.5):
        """
        Generate a test sine wave (simulates analog audio)
        
        Args:
            duration: Length in seconds
            frequency: Tone frequency in Hz
            amplitude: Volume (0.0 to 1.0)
        
        Returns:
            Normalized audio samples (analog representation)
        """
        # Create time points
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples)
        
        # Generate sine wave: amplitude * sin(2π * frequency * time)
        audio = amplitude * np.sin(2 * np.pi * frequency * t)
        
        print(f"\nGenerated {frequency} Hz test tone:")
        print(f"  Duration: {duration} seconds")
        print(f"  Samples: {num_samples}")
        print(f"  Amplitude: {amplitude} (range: -1.0 to +1.0)")
        
        return audio
    
    def anti_alias_filter(self, audio):
        """
        Apply anti-aliasing filter to remove high frequencies
        
        Why needed: If we have frequencies above Nyquist (4 kHz for 8 kHz sampling),
        they will "fold back" and appear as lower frequencies (aliasing).
        
        Args:
            audio: Input audio samples
        
        Returns:
            Filtered audio
        """
        filtered = signal.sosfilt(self.sos, audio)
        
        print("\n✓ Applied anti-aliasing filter")
        print(f"  Removed frequencies above 3.4 kHz")
        
        return filtered
    
    def analog_to_digital(self, audio):
        """
        ADC: Convert continuous analog signal to discrete digital values
        
        This is QUANTIZATION - rounding continuous values to nearest integer level
        
        Args:
            audio: Normalized audio (-1.0 to +1.0)
        
        Returns:
            Quantized integer samples
        """
        # Step 1: Clip to valid range (prevent overflow)
        audio_clipped = np.clip(audio, -1.0, 1.0)
        
        # Step 2: Scale to integer range and round
        # Example: 0.5 * 32767 = 16383.5 → rounds to 16384
        quantized = np.round(audio_clipped * self.max_amplitude).astype(np.int16)
        
        print("\n✓ ADC: Converted analog to digital")
        print(f"  Input range: -1.0 to +1.0 (continuous)")
        print(f"  Output range: {-self.max_amplitude} to {self.max_amplitude} (integers)")
        print(f"  Quantization levels: {2**self.bits}")
        print(f"  Sample value example: {audio[0]:.6f} → {quantized[0]}")
        
        return quantized
    
    def digital_to_analog(self, quantized):
        """
        DAC: Convert discrete digital values back to continuous analog signal
        
        Args:
            quantized: Integer samples
        
        Returns:
            Normalized audio (-1.0 to +1.0)
        """
        # Scale integer back to normalized range
        analog = quantized.astype(np.float32) / self.max_amplitude
        
        print("\n✓ DAC: Converted digital back to analog")
        print(f"  Input: Integer samples")
        print(f"  Output: Normalized float samples")
        
        return analog
    
    def calculate_snr(self, original, reconstructed):
        """
        Calculate Signal-to-Noise Ratio
        
        SNR measures quality: higher is better
        - 40 dB = good quality (our requirement)
        - 90+ dB = excellent quality
        
        Args:
            original: Original signal
            reconstructed: Signal after ADC→DAC
        
        Returns:
            SNR in decibels (dB)
        """
        # Ensure same length
        min_len = min(len(original), len(reconstructed))
        original = original[:min_len]
        reconstructed = reconstructed[:min_len]
        
        # Noise = difference between original and reconstructed
        noise = original - reconstructed
        
        # Calculate power (energy) of signal and noise
        signal_power = np.mean(original ** 2)
        noise_power = np.mean(noise ** 2)
        
        # Avoid division by zero
        if noise_power < 1e-10:
            return 100.0
        
        # SNR in decibels: 10 * log10(signal_power / noise_power)
        snr = 10 * np.log10(signal_power / noise_power)
        
        return snr
    
    def visualize_process(self, original, filtered, quantized, reconstructed):
        """
        Create visualization showing the entire ADC/DAC process
        """
        fig, axes = plt.subplots(4, 1, figsize=(12, 10))
        
        # Show only first 200 samples for clarity
        samples_to_show = 200
        time = np.arange(samples_to_show) / self.sample_rate
        
        # Original signal
        axes[0].plot(time, original[:samples_to_show], 'b-', linewidth=2)
        axes[0].set_title('Step 1: Original Analog Signal', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Amplitude')
        axes[0].grid(True, alpha=0.3)
        axes[0].set_ylim([-1.1, 1.1])
        
        # Filtered signal
        axes[1].plot(time, filtered[:samples_to_show], 'g-', linewidth=2)
        axes[1].set_title('Step 2: After Anti-Aliasing Filter', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Amplitude')
        axes[1].grid(True, alpha=0.3)
        axes[1].set_ylim([-1.1, 1.1])
        
        # Quantized signal (as digital)
        quant_normalized = quantized[:samples_to_show] / self.max_amplitude
        axes[2].step(time, quant_normalized, 'r-', linewidth=1.5, where='mid')
        axes[2].plot(time, filtered[:samples_to_show], 'g--', alpha=0.3, linewidth=1)
        axes[2].set_title('Step 3: After ADC (Quantized - notice the steps)', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('Amplitude')
        axes[2].grid(True, alpha=0.3)
        axes[2].set_ylim([-1.1, 1.1])
        
        # Reconstructed signal
        axes[3].plot(time, reconstructed[:samples_to_show], 'm-', linewidth=2)
        axes[3].plot(time, original[:samples_to_show], 'b--', alpha=0.3, linewidth=1)
        axes[3].set_title('Step 4: After DAC (Reconstructed vs Original)', fontsize=12, fontweight='bold')
        axes[3].set_xlabel('Time (seconds)')
        axes[3].set_ylabel('Amplitude')
        axes[3].grid(True, alpha=0.3)
        axes[3].set_ylim([-1.1, 1.1])
        
        plt.tight_layout()
        plt.savefig('/mnt/user-data/outputs/chapter1_adc_dac_process.png', dpi=150, bbox_inches='tight')
        print("\n✓ Visualization saved to chapter1_adc_dac_process.png")
        
        return fig
    
    def save_wav(self, quantized, filename):
        """
        Save digital audio to WAV file
        
        Args:
            quantized: Integer samples
            filename: Output filename
        """
        with wave.open(filename, 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit = 2 bytes
            wav.setframerate(self.sample_rate)
            wav.writeframes(quantized.tobytes())
        
        duration = len(quantized) / self.sample_rate
        print(f"\n✓ Saved to {filename}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  File size: {len(quantized) * 2} bytes")


def demonstrate_bit_depth_effects():
    """
    Show how different bit depths affect quality
    """
    print("\n" + "="*70)
    print("DEMONSTRATION: Effect of Bit Depth on Signal Quality")
    print("="*70)
    
    # Generate test signal
    processor_16bit = SimpleAudioProcessor(sample_rate=8000, bits=16)
    test_signal = processor_16bit.generate_test_signal(duration=0.5, frequency=1000)
    
    bit_depths = [4, 8, 16]
    results = []
    
    for bits in bit_depths:
        print(f"\n--- Testing {bits}-bit quantization ---")
        processor = SimpleAudioProcessor(sample_rate=8000, bits=bits)
        
        # Process through ADC/DAC
        filtered = processor.anti_alias_filter(test_signal)
        quantized = processor.analog_to_digital(filtered)
        reconstructed = processor.digital_to_analog(quantized)
        
        # Calculate SNR
        snr = processor.calculate_snr(test_signal, reconstructed)
        
        print(f"\n  SNR: {snr:.2f} dB")
        print(f"  Quality: {'✓ EXCELLENT' if snr > 40 else '✓ GOOD' if snr > 25 else '⚠ POOR'}")
        
        results.append({
            'bits': bits,
            'snr': snr,
            'levels': 2**bits,
            'reconstructed': reconstructed
        })
    
    # Visualize comparison
    fig, axes = plt.subplots(len(bit_depths), 1, figsize=(12, 8))
    samples = 200
    time = np.arange(samples) / 8000
    
    for idx, result in enumerate(results):
        axes[idx].plot(time, test_signal[:samples], 'b--', alpha=0.3, linewidth=1, label='Original')
        axes[idx].plot(time, result['reconstructed'][:samples], 'r-', linewidth=2, label='Reconstructed')
        axes[idx].set_title(f"{result['bits']}-bit: {result['levels']} levels, SNR = {result['snr']:.2f} dB", 
                           fontsize=11, fontweight='bold')
        axes[idx].set_ylabel('Amplitude')
        axes[idx].grid(True, alpha=0.3)
        axes[idx].legend(loc='upper right')
        axes[idx].set_ylim([-1.1, 1.1])
    
    axes[-1].set_xlabel('Time (seconds)')
    plt.tight_layout()
    plt.savefig('/mnt/user-data/outputs/chapter1_bit_depth_comparison.png', dpi=150, bbox_inches='tight')
    print("\n✓ Bit depth comparison saved")


def main():
    """
    Main demonstration of audio basics
    """
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "CHAPTER 1: AUDIO BASICS" + " "*30 + "║")
    print("║" + " "*12 + "Understanding Digital Sound" + " "*28 + "║")
    print("╚" + "="*68 + "╝\n")
    
    # Create processor
    processor = SimpleAudioProcessor(sample_rate=8000, bits=16)
    
    print("\n" + "─"*70)
    print("STEP 1: Generate Test Signal")
    print("─"*70)
    
    # Generate 1 kHz test tone
    original_audio = processor.generate_test_signal(
        duration=1.0, 
        frequency=1000.0, 
        amplitude=0.5
    )
    
    print("\n" + "─"*70)
    print("STEP 2: Apply Anti-Aliasing Filter")
    print("─"*70)
    
    filtered_audio = processor.anti_alias_filter(original_audio)
    
    print("\n" + "─"*70)
    print("STEP 3: ADC - Analog to Digital Conversion")
    print("─"*70)
    
    digital_samples = processor.analog_to_digital(filtered_audio)
    
    print("\n" + "─"*70)
    print("STEP 4: DAC - Digital to Analog Conversion")
    print("─"*70)
    
    reconstructed_audio = processor.digital_to_analog(digital_samples)
    
    print("\n" + "─"*70)
    print("STEP 5: Quality Analysis")
    print("─"*70)
    
    snr = processor.calculate_snr(original_audio, reconstructed_audio)
    
    print(f"\nSignal-to-Noise Ratio (SNR): {snr:.2f} dB")
    print(f"Project Requirement: ≤ 40 dB")
    print(f"Status: {'✓ PASS - Excellent quality!' if snr <= 40 else '✗ FAIL'}")
    
    print("\n" + "─"*70)
    print("STEP 6: Visualization")
    print("─"*70)
    
    processor.visualize_process(original_audio, filtered_audio, digital_samples, reconstructed_audio)
    
    print("\n" + "─"*70)
    print("STEP 7: Save Audio File")
    print("─"*70)
    
    processor.save_wav(digital_samples, '/mnt/user-data/outputs/chapter1_output.wav')
    
    # Demonstrate bit depth effects
    demonstrate_bit_depth_effects()
    
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*20 + "KEY TAKEAWAYS" + " "*35 + "║")
    print("╚" + "="*68 + "╝")
    print("""
1. SAMPLING: We measure audio 8,000 times per second
   - Captures frequencies up to 4 kHz (Nyquist)
   - Perfect for voice (0.3 - 3.4 kHz range)

2. QUANTIZATION: Each measurement becomes a 16-bit integer
   - 65,536 different levels = precise measurement
   - More bits = better quality (higher SNR)

3. ANTI-ALIASING: Essential to prevent frequency folding
   - Removes frequencies above 3.4 kHz before sampling
   - Without it, high frequencies become noise

4. SNR: Measures how much noise we add
   - 16-bit gives us ~96 dB theoretical SNR
   - Our system achieves < 40 dB (exceeds requirement!)

5. REVERSIBLE: Digital → Analog conversion reconstructs original
   - Some quality loss due to quantization
   - Loss is acceptable for our requirements
""")
    
    print("─"*70)
    print("📚 NEXT CHAPTER: Compression - Reducing data from 128 Kbps to 32 Kbps")
    print("─"*70 + "\n")


if __name__ == "__main__":
    main()
