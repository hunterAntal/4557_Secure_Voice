"""
System Integration Tests
Validates all requirements and security features
"""

import numpy as np
import time
from audio_processor import AudioProcessor
from crypto_module import CryptoModule
from error_correction import ErrorCorrection


class SystemTester:
    """
    Comprehensive system testing
    """

    def __init__(self):
        self.results = []

    def print_header(self, title: str):
        """Print test section header"""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)

    def print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result"""
        status = " PASS" if passed else "✗ FAIL"
        print(f"\n{status} - {name}")
        if details:
            print(f"  {details}")

        self.results.append({
            'name': name,
            'passed': passed,
            'details': details
        })

    def test_snr_requirement(self):
        """Test SNR ≤ 40 dB requirement"""
        self.print_header("TEST 1: SNR Requirement (≤ 40 dB)")

        processor = AudioProcessor(sample_rate=8000, bits=16)

        # Test with different signals
        test_signals = [
            ("1 kHz sine wave", lambda t: 0.5 * np.sin(2 * np.pi * 1000 * t)),
            ("440 Hz tone (A4)", lambda t: 0.3 * np.sin(2 * np.pi * 440 * t)),
            ("Complex waveform", lambda t: 0.3 * (np.sin(2 * np.pi * 440 * t) +
                                                   0.5 * np.sin(2 * np.pi * 880 * t))),
        ]

        all_passed = True

        for signal_name, signal_func in test_signals:
            # Generate signal
            duration = 1.0
            t = np.linspace(0, duration, int(processor.sample_rate * duration))
            signal = signal_func(t)

            # Process through complete pipeline
            compressed, num_samples = processor.process_for_transmission(signal)
            reconstructed = processor.process_for_playback(compressed, num_samples)

            # Calculate SNR
            snr = processor.calculate_snr(signal, reconstructed)

            passed = snr <= 40.0
            all_passed = all_passed and passed

            self.print_test(
                f"SNR test - {signal_name}",
                passed,
                f"SNR = {snr:.2f} dB (requirement: ≤ 40 dB)"
            )

        return all_passed

    def test_data_rate(self):
        """Test 64 Kbps data rate requirement"""
        self.print_header("TEST 2: Data Rate (≤ 64 Kbps error-free)")

        processor = AudioProcessor(sample_rate=8000, bits=16)
        ec = ErrorCorrection(nsym=32)

        # Generate 1 second of audio
        duration = 1.0
        t = np.linspace(0, duration, int(processor.sample_rate * duration))
        signal = 0.5 * np.sin(2 * np.pi * 1000 * t)

        # Process
        compressed, num_samples = processor.process_for_transmission(signal)
        ec_data = ec.encode(compressed)

        # Calculate bitrate
        total_bits = len(ec_data) * 8
        bitrate_kbps = total_bits / duration / 1000

        passed = bitrate_kbps <= 64.0

        self.print_test(
            "Data rate test",
            passed,
            f"Bitrate = {bitrate_kbps:.2f} Kbps (requirement: ≤ 64 Kbps)"
        )

        # Additional metrics
        print(f"\n  Breakdown:")
        print(f"    Original PCM: {num_samples * 2 * 8 / 1000:.2f} Kbps")
        print(f"    After ADPCM:  {len(compressed) * 8 / 1000:.2f} Kbps")
        print(f"    After Reed-Solomon: {bitrate_kbps:.2f} Kbps")
        print(f"    Compression ratio: {(num_samples * 2) / len(compressed):.2f}:1")

        return passed

    def test_encryption(self):
        """Test encryption against eavesdropping"""
        self.print_header("TEST 3: Encryption (Eavesdropping Protection)")

        # Initialize crypto modules
        sender = CryptoModule()
        receiver = CryptoModule()

        # Generate keys
        sender_priv, sender_pub = sender.generate_rsa_keypair()
        receiver_priv, receiver_pub = receiver.generate_rsa_keypair()

        # Exchange public keys
        sender.load_peer_public_key(receiver_pub)
        receiver.load_peer_public_key(sender_pub)

        # Establish session
        encrypted_keys = sender.generate_session_keys()
        receiver.receive_session_keys(encrypted_keys)

        # Test data
        test_message = b"Secret voice data: Attack at dawn!"

        # Encrypt
        encrypted = sender.create_secure_packet(test_message)

        # Verify eavesdropper cannot decrypt (without keys)
        eavesdropper = CryptoModule()
        eavesdropper_priv, eavesdropper_pub = eavesdropper.generate_rsa_keypair()

        # Eavesdropper tries to decrypt
        decrypted_by_eavesdropper = None
        try:
            # This should fail
            decrypted_by_eavesdropper = eavesdropper.verify_secure_packet(encrypted)
        except:
            pass

        test1_passed = decrypted_by_eavesdropper is None
        self.print_test(
            "Eavesdropper cannot decrypt",
            test1_passed,
            "Encrypted data cannot be read without proper keys"
        )

        # Legitimate receiver can decrypt
        decrypted = receiver.verify_secure_packet(encrypted)
        test2_passed = decrypted == test_message

        self.print_test(
            "Legitimate receiver can decrypt",
            test2_passed,
            f"Decrypted data matches original"
        )

        return test1_passed and test2_passed

    def test_authentication(self):
        """Test authentication against imposter clients"""
        self.print_header("TEST 4: Authentication (Imposter Protection)")

        # Initialize crypto modules
        legitimate = CryptoModule()
        server = CryptoModule()
        imposter = CryptoModule()

        # Generate keys
        legit_priv, legit_pub = legitimate.generate_rsa_keypair()
        server_priv, server_pub = server.generate_rsa_keypair()
        imposter_priv, imposter_pub = imposter.generate_rsa_keypair()

        # Server knows legitimate client's public key
        server.load_peer_public_key(legit_pub)

        # Create challenge
        challenge = b"Authenticate yourself!"

        # Legitimate client signs
        legit_signature = legitimate.sign_message(challenge)

        # Server verifies legitimate signature
        test1_passed = server.verify_signature(challenge, legit_signature)

        self.print_test(
            "Legitimate client authenticated",
            test1_passed,
            "Valid signature accepted"
        )

        # Imposter tries to sign
        imposter_signature = imposter.sign_message(challenge)

        # Server rejects imposter
        test2_passed = not server.verify_signature(challenge, imposter_signature)

        self.print_test(
            "Imposter client rejected",
            test2_passed,
            "Invalid signature rejected"
        )

        return test1_passed and test2_passed

    def test_integrity(self):
        """Test integrity protection against content manipulation"""
        self.print_header("TEST 5: Integrity (Manipulation Protection)")

        # Initialize crypto modules
        sender = CryptoModule()
        receiver = CryptoModule()

        # Generate and exchange keys
        sender_priv, sender_pub = sender.generate_rsa_keypair()
        receiver_priv, receiver_pub = receiver.generate_rsa_keypair()

        sender.load_peer_public_key(receiver_pub)
        receiver.load_peer_public_key(sender_pub)

        encrypted_keys = sender.generate_session_keys()
        receiver.receive_session_keys(encrypted_keys)

        # Original message
        original = b"Original voice data"

        # Create secure packet
        packet = sender.create_secure_packet(original)

        # Test 1: Unmodified packet verifies
        decrypted = receiver.verify_secure_packet(packet)
        test1_passed = decrypted == original

        self.print_test(
            "Unmodified packet accepted",
            test1_passed,
            "Integrity check passes for valid data"
        )

        # Test 2: Modified packet rejected
        # Tamper with packet
        tampered = bytearray(packet)
        tampered[len(packet) // 2] ^= 0xFF  # Flip bits in middle

        decrypted_tampered = receiver.verify_secure_packet(bytes(tampered))
        test2_passed = decrypted_tampered is None

        self.print_test(
            "Tampered packet rejected",
            test2_passed,
            "Integrity check detects modification"
        )

        # Test 3: Replay attack detection
        # Reset receiver sequence
        receiver.expected_sequence = 100  # Expect future packet

        decrypted_replay = receiver.verify_secure_packet(packet)
        test3_passed = decrypted_replay is None

        self.print_test(
            "Replay attack prevented",
            test3_passed,
            "Out-of-sequence packets rejected"
        )

        return test1_passed and test2_passed and test3_passed

    def test_error_correction(self):
        """Test error correction capability"""
        self.print_header("TEST 6: Error Correction (64 Kbps error-free)")

        ec = ErrorCorrection(nsym=32)

        # Test data
        test_data = b"Voice data packet" * 20

        # Test different error rates
        error_rates = [0.001, 0.005, 0.01]
        all_passed = True

        for error_rate in error_rates:
            # Encode
            encoded = ec.encode(test_data)

            # Simulate channel errors
            corrupted = ec.simulate_channel_errors(encoded, error_rate)

            # Count errors
            bit_errors = sum(bin(a ^ b).count('1') for a, b in zip(encoded, corrupted))

            # Decode
            decoded, errors_corrected = ec.decode(corrupted)

            # Verify
            passed = decoded == test_data

            all_passed = all_passed and passed

            self.print_test(
                f"Error correction at {error_rate:.3f} error rate",
                passed,
                f"{bit_errors} bit errors introduced, {errors_corrected} corrected"
            )

        return all_passed

    def test_performance(self):
        """Test system performance metrics"""
        self.print_header("TEST 7: Performance Metrics")

        processor = AudioProcessor(sample_rate=8000, bits=16)
        crypto = CryptoModule()
        ec = ErrorCorrection(nsym=32)

        # Generate test audio
        duration = 1.0
        t = np.linspace(0, duration, int(processor.sample_rate * duration))
        signal = 0.5 * np.sin(2 * np.pi * 1000 * t)

        # Setup crypto (don't time key generation - one-time cost)
        crypto.generate_rsa_keypair()
        crypto.session_key = b'0' * 32
        crypto.hmac_key = b'0' * 32

        # Measure processing time (actual per-packet cost)
        start = time.time()

        # Audio processing
        compressed, num_samples = processor.process_for_transmission(signal)

        # Error correction
        ec_data = ec.encode(compressed)

        # Encryption
        encrypted = crypto.create_secure_packet(ec_data)

        processing_time = time.time() - start

        # Calculate latency
        latency_ms = processing_time * 1000

        passed = latency_ms < 500  # Less than 500ms acceptable for voice

        self.print_test(
            "Processing latency",
            passed,
            f"{latency_ms:.2f} ms (target: < 500 ms)"
        )

        # Memory usage
        total_size = len(encrypted)
        memory_efficiency = (len(signal.tobytes()) / total_size) * 100

        print(f"\n  Memory usage:")
        print(f"    Original: {len(signal.tobytes())} bytes")
        print(f"    Compressed: {len(compressed)} bytes")
        print(f"    With EC: {len(ec_data)} bytes")
        print(f"    Encrypted: {total_size} bytes")
        print(f"    Efficiency: {memory_efficiency:.1f}%")

        return passed

    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "█" * 80)
        print(" SECURE VOICE TRANSMISSION SYSTEM - VALIDATION TEST SUITE")
        print("█" * 80)

        tests = [
            ("SNR Requirement", self.test_snr_requirement),
            ("Data Rate", self.test_data_rate),
            ("Encryption", self.test_encryption),
            ("Authentication", self.test_authentication),
            ("Integrity", self.test_integrity),
            ("Error Correction", self.test_error_correction),
            ("Performance", self.test_performance),
        ]

        # Run all tests
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"\n✗ {test_name} - ERROR: {e}")
                import traceback
                traceback.print_exc()

        # Summary
        self.print_header("TEST SUMMARY")

        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        print(f"\nTotal tests: {total}")
        print(f"Passed: {passed} ")
        print(f"Failed: {failed} ✗")
        print(f"Success rate: {(passed / total * 100):.1f}%")

        if failed == 0:
            print("\n" + "█" * 80)
            print("  ALL REQUIREMENTS MET - SYSTEM VALIDATED")
            print("█" * 80)
        else:
            print("\n" + "█" * 80)
            print(f" ✗ {failed} TEST(S) FAILED - REVIEW REQUIRED")
            print("█" * 80)

        return failed == 0


if __name__ == "__main__":
    tester = SystemTester()
    success = tester.run_all_tests()

    exit(0 if success else 1)
