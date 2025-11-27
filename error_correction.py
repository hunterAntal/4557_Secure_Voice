"""
Error Correction Module
Implements Reed-Solomon forward error correction for reliable transmission
"""

from reedsolo import RSCodec
import numpy as np
from typing import Tuple


class ErrorCorrection:
    """
    Provides Reed-Solomon error correction coding

    Reed-Solomon (255, 223) code:
    - Can correct up to 16 symbol errors per block
    - Overhead: 32 bytes per 223 bytes (~14% overhead)
    - Enables error-free transmission at 64 Kbps over noisy channels
    """

    def __init__(self, nsym: int = 32):
        """
        Initialize Reed-Solomon codec

        Args:
            nsym: Number of error correction symbols (default 32)
                  Can correct up to nsym/2 errors
        """
        self.nsym = nsym  # Error correction symbols
        self.max_errors = nsym // 2  # Maximum correctable errors
        self.rs = RSCodec(nsym)

        # Block size: 255 - nsym for RS(255, 223)
        self.data_size = 255 - nsym

    def encode(self, data: bytes) -> bytes:
        """
        Encode data with Reed-Solomon error correction

        Args:
            data: Raw data bytes

        Returns:
            Encoded data with error correction codes
        """
        # Pad data to multiple of data_size if needed
        padding_len = 0
        if len(data) % self.data_size != 0:
            padding_len = self.data_size - (len(data) % self.data_size)
            data = data + b'\x00' * padding_len

        # Encode in blocks
        encoded_blocks = []
        for i in range(0, len(data), self.data_size):
            block = data[i:i + self.data_size]
            encoded_block = self.rs.encode(block)
            encoded_blocks.append(encoded_block)

        # Prepend padding length (1 byte) for decoding
        encoded_data = bytes([padding_len]) + b''.join(encoded_blocks)

        return encoded_data

    def decode(self, encoded_data: bytes) -> Tuple[bytes, int]:
        """
        Decode Reed-Solomon encoded data and correct errors

        Args:
            encoded_data: Encoded data with error correction

        Returns:
            Tuple of (decoded_data, num_errors_corrected)
        """
        # Extract padding length
        padding_len = encoded_data[0]
        encoded_data = encoded_data[1:]

        # Decode in blocks
        decoded_blocks = []
        total_errors = 0

        block_size = 255  # RS(255, 223) produces 255-byte blocks

        for i in range(0, len(encoded_data), block_size):
            block = encoded_data[i:i + block_size]

            try:
                # Decode and error correction
                decoded_block, _, errors_fixed = self.rs.decode(block)
                decoded_blocks.append(bytes(decoded_block))

                # errors_fixed is a bytearray of error positions
                total_errors += len(errors_fixed)

            except Exception as e:
                # Too many errors to correct
                print(f"Error correction failed for block {i // block_size}: {e}")
                # Return partial data with error flag
                decoded_blocks.append(b'\x00' * self.data_size)
                total_errors = -1  # Indicate failure

        # Combine blocks and remove padding
        decoded_data = b''.join(decoded_blocks)

        if padding_len > 0:
            decoded_data = decoded_data[:-padding_len]

        return decoded_data, total_errors

    def calculate_overhead(self) -> float:
        """
        Calculate encoding overhead percentage

        Returns:
            Overhead as percentage
        """
        overhead = (self.nsym / self.data_size) * 100
        return overhead

    def get_code_rate(self) -> float:
        """
        Calculate code rate (information / total)

        Returns:
            Code rate (0 to 1)
        """
        return self.data_size / 255

    def simulate_channel_errors(self, data: bytes, error_rate: float) -> bytes:
        """
        Simulate random bit errors in transmitted data

        Args:
            data: Clean data
            error_rate: Probability of bit error (0 to 1)

        Returns:
            Data with simulated errors
        """
        data_array = bytearray(data)

        for i in range(len(data_array)):
            for bit in range(8):
                if np.random.random() < error_rate:
                    # Flip bit
                    data_array[i] ^= (1 << bit)

        return bytes(data_array)

    def test_error_correction(self, data: bytes, error_rate: float) -> dict:
        """
        Test error correction capability

        Args:
            data: Test data
            error_rate: Simulated error rate

        Returns:
            Dictionary with test results
        """
        # Encode
        encoded = self.encode(data)

        # Simulate channel errors
        corrupted = self.simulate_channel_errors(encoded, error_rate)

        # Count bit errors
        bit_errors = sum(bin(a ^ b).count('1') for a, b in zip(encoded, corrupted))

        # Decode
        decoded, errors_corrected = self.decode(corrupted)

        # Check if data recovered correctly
        success = (decoded == data)

        results = {
            'original_size': len(data),
            'encoded_size': len(encoded),
            'overhead_percent': self.calculate_overhead(),
            'bit_errors_introduced': bit_errors,
            'errors_corrected': errors_corrected,
            'correction_successful': success,
            'error_rate': error_rate
        }

        return results


class AdaptiveErrorCorrection:
    """
    Adaptive error correction that adjusts strength based on channel conditions
    """

    def __init__(self):
        """Initialize with multiple error correction levels"""
        # Different RS configurations
        self.levels = {
            'low': ErrorCorrection(nsym=16),    # Light protection
            'medium': ErrorCorrection(nsym=32),  # Standard protection
            'high': ErrorCorrection(nsym=64)     # Heavy protection
        }
        self.current_level = 'medium'
        self.error_history = []
        self.history_size = 10

    def encode(self, data: bytes) -> Tuple[bytes, str]:
        """
        Encode with current error correction level

        Args:
            data: Data to encode

        Returns:
            Tuple of (encoded_data, level_used)
        """
        encoder = self.levels[self.current_level]
        encoded = encoder.encode(data)
        return encoded, self.current_level

    def decode(self, encoded_data: bytes, level: str) -> Tuple[bytes, int]:
        """
        Decode with specified error correction level

        Args:
            encoded_data: Encoded data
            level: Error correction level used

        Returns:
            Tuple of (decoded_data, errors_corrected)
        """
        decoder = self.levels[level]
        decoded, errors = decoder.decode(encoded_data)

        # Update error history for adaptation
        self.error_history.append(errors)
        if len(self.error_history) > self.history_size:
            self.error_history.pop(0)

        # Adapt error correction level
        self._adapt_level()

        return decoded, errors

    def _adapt_level(self):
        """Adapt error correction level based on recent error rates"""
        if len(self.error_history) < 3:
            return

        avg_errors = sum(self.error_history) / len(self.error_history)

        # Thresholds for level switching
        if avg_errors > 10 and self.current_level != 'high':
            print(f"Increasing error correction: {self.current_level} -> high")
            self.current_level = 'high'
        elif avg_errors < 3 and self.current_level == 'high':
            print(f"Decreasing error correction: {self.current_level} -> medium")
            self.current_level = 'medium'
        elif avg_errors > 5 and self.current_level == 'low':
            print(f"Increasing error correction: {self.current_level} -> medium")
            self.current_level = 'medium'
        elif avg_errors < 1 and self.current_level == 'medium':
            print(f"Decreasing error correction: {self.current_level} -> low")
            self.current_level = 'low'


if __name__ == "__main__":
    print("Testing Reed-Solomon Error Correction...")

    # Initialize error correction
    ec = ErrorCorrection(nsym=32)

    print(f"\nConfiguration:")
    print(f"  Code: RS(255, {ec.data_size})")
    print(f"  Max correctable errors: {ec.max_errors} symbols per block")
    print(f"  Overhead: {ec.calculate_overhead():.1f}%")
    print(f"  Code rate: {ec.get_code_rate():.3f}")

    # Test data
    test_data = b"This is a test voice packet that needs error protection!" * 10
    print(f"\nTest data size: {len(test_data)} bytes")

    # Test different error rates
    error_rates = [0.001, 0.005, 0.01, 0.02]

    print("\nTesting error correction at different error rates:")
    print("-" * 80)

    for rate in error_rates:
        results = ec.test_error_correction(test_data, rate)

        print(f"\nError rate: {rate:.3f} ({rate * 100:.1f}%)")
        print(f"  Bit errors introduced: {results['bit_errors_introduced']}")
        print(f"  Errors corrected: {results['errors_corrected']}")
        print(f"  Success: {'✓' if results['correction_successful'] else '✗'}")

    # Test adaptive error correction
    print("\n" + "=" * 80)
    print("Testing Adaptive Error Correction...")
    print("=" * 80)

    adaptive = AdaptiveErrorCorrection()

    # Simulate varying channel conditions
    print("\nSimulating varying channel conditions:")
    conditions = [
        ('good', 0.001),
        ('good', 0.001),
        ('degraded', 0.01),
        ('poor', 0.02),
        ('poor', 0.025),
        ('recovering', 0.01),
        ('good', 0.001)
    ]

    for condition, error_rate in conditions:
        # Encode
        encoded, level = adaptive.encode(test_data)

        # Simulate errors
        corrupted = adaptive.levels['medium'].simulate_channel_errors(encoded, error_rate)

        # Decode
        decoded, errors = adaptive.decode(corrupted, level)

        success = decoded == test_data
        print(f"  {condition:12s} (err={error_rate:.3f}): level={level:6s}, "
              f"errors={errors:3d}, success={'✓' if success else '✗'}")

    print("\n✓ Error correction tests complete!")
