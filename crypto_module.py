"""
Cryptographic Security Module
Provides encryption, authentication, and integrity protection
"""

from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256, HMAC
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_OAEP
import json
import time
from typing import Tuple, Optional, Dict
import struct


class CryptoModule:
    """
    Handles all cryptographic operations for secure voice transmission

    Security Features:
    - AES-256-GCM: Authenticated encryption for voice data
    - RSA-2048: Key exchange and digital signatures
    - HMAC-SHA256: Additional message authentication
    - Sequence numbers: Prevent replay attacks
    """

    def __init__(self):
        """Initialize cryptographic module"""
        self.rsa_key = None
        self.rsa_public_key = None
        self.peer_public_key = None
        self.session_key = None
        self.hmac_key = None
        self.sequence_number = 0
        self.expected_sequence = 0
        self.session_start_time = None
        self.key_rotation_interval = 3600  # Rotate keys every hour

    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair for asymmetric operations

        Args:
            key_size: Key size in bits (2048 for security)

        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        key = RSA.generate(key_size)
        self.rsa_key = key

        private_pem = key.export_key()
        public_pem = key.publickey().export_key()

        return private_pem, public_pem

    def load_private_key(self, private_key_pem: bytes):
        """Load RSA private key from PEM format"""
        self.rsa_key = RSA.import_key(private_key_pem)

    def load_peer_public_key(self, public_key_pem: bytes):
        """Load peer's RSA public key from PEM format"""
        self.peer_public_key = RSA.import_key(public_key_pem)

    def generate_session_keys(self) -> bytes:
        """
        Generate new session keys for AES and HMAC

        Returns:
            Encrypted session key bundle (for transmission to peer)
        """
        # Generate 256-bit AES key and 256-bit HMAC key
        self.session_key = get_random_bytes(32)  # AES-256
        self.hmac_key = get_random_bytes(32)     # HMAC-SHA256

        # Reset sequence numbers
        self.sequence_number = 0
        self.expected_sequence = 0
        self.session_start_time = time.time()

        # Bundle keys together
        key_bundle = {
            'aes_key': self.session_key.hex(),
            'hmac_key': self.hmac_key.hex(),
            'timestamp': self.session_start_time
        }

        # Encrypt with peer's public key
        if self.peer_public_key is None:
            raise ValueError("Peer public key not loaded")

        cipher_rsa = PKCS1_OAEP.new(self.peer_public_key)
        encrypted_bundle = cipher_rsa.encrypt(json.dumps(key_bundle).encode())

        return encrypted_bundle

    def receive_session_keys(self, encrypted_bundle: bytes) -> bool:
        """
        Decrypt and install session keys from peer

        Args:
            encrypted_bundle: RSA-encrypted session key bundle

        Returns:
            True if successful
        """
        if self.rsa_key is None:
            raise ValueError("Private key not loaded")

        try:
            # Decrypt with our private key
            cipher_rsa = PKCS1_OAEP.new(self.rsa_key)
            decrypted = cipher_rsa.decrypt(encrypted_bundle)

            # Parse key bundle
            key_bundle = json.loads(decrypted.decode())

            self.session_key = bytes.fromhex(key_bundle['aes_key'])
            self.hmac_key = bytes.fromhex(key_bundle['hmac_key'])
            self.session_start_time = key_bundle['timestamp']
            self.expected_sequence = 0

            return True
        except Exception as e:
            print(f"Error receiving session keys: {e}")
            return False

    def sign_message(self, message: bytes) -> bytes:
        """
        Create digital signature for message authentication

        Args:
            message: Message to sign

        Returns:
            Digital signature
        """
        if self.rsa_key is None:
            raise ValueError("Private key not loaded")

        h = SHA256.new(message)
        signature = pkcs1_15.new(self.rsa_key).sign(h)
        return signature

    def verify_signature(self, message: bytes, signature: bytes) -> bool:
        """
        Verify digital signature (authenticates sender)

        Args:
            message: Original message
            signature: Digital signature to verify

        Returns:
            True if signature is valid
        """
        if self.peer_public_key is None:
            raise ValueError("Peer public key not loaded")

        h = SHA256.new(message)
        try:
            pkcs1_15.new(self.peer_public_key).verify(h, signature)
            return True
        except (ValueError, TypeError):
            return False

    def check_key_rotation(self) -> bool:
        """
        Check if session keys should be rotated

        Returns:
            True if rotation needed
        """
        if self.session_start_time is None:
            return True

        elapsed = time.time() - self.session_start_time
        return elapsed >= self.key_rotation_interval

    def encrypt_packet(self, plaintext: bytes, associated_data: bytes = b'') -> bytes:
        """
        Encrypt data packet with AES-256-GCM

        Packet format: [nonce(16)] [seq(4)] [ciphertext] [tag(16)]

        Args:
            plaintext: Data to encrypt
            associated_data: Additional authenticated data (not encrypted)

        Returns:
            Encrypted packet with authentication tag
        """
        if self.session_key is None:
            raise ValueError("Session key not established")

        # Generate random nonce (96 bits recommended for GCM)
        nonce = get_random_bytes(16)

        # Include sequence number in AAD to prevent reordering
        seq_bytes = struct.pack('!I', self.sequence_number)
        full_aad = associated_data + seq_bytes

        # Encrypt with AES-GCM
        cipher = AES.new(self.session_key, AES.MODE_GCM, nonce=nonce)
        cipher.update(full_aad)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

        # Construct packet
        packet = nonce + seq_bytes + ciphertext + tag

        # Increment sequence number
        self.sequence_number += 1

        return packet

    def decrypt_packet(self, packet: bytes, associated_data: bytes = b'') -> Optional[bytes]:
        """
        Decrypt and verify data packet

        Args:
            packet: Encrypted packet
            associated_data: Additional authenticated data

        Returns:
            Decrypted plaintext or None if verification fails
        """
        if self.session_key is None:
            raise ValueError("Session key not established")

        try:
            # Parse packet
            nonce = packet[:16]
            seq_bytes = packet[16:20]
            ciphertext = packet[20:-16]
            tag = packet[-16:]

            # Check sequence number (basic replay protection)
            seq_num = struct.unpack('!I', seq_bytes)[0]
            if seq_num < self.expected_sequence:
                print(f"Warning: Out-of-order packet (expected {self.expected_sequence}, got {seq_num})")
                return None

            self.expected_sequence = seq_num + 1

            # Prepare AAD
            full_aad = associated_data + seq_bytes

            # Decrypt with verification
            cipher = AES.new(self.session_key, AES.MODE_GCM, nonce=nonce)
            cipher.update(full_aad)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)

            return plaintext

        except (ValueError, KeyError) as e:
            print(f"Decryption/verification failed: {e}")
            return None

    def compute_hmac(self, data: bytes) -> bytes:
        """
        Compute HMAC-SHA256 for additional integrity protection

        Args:
            data: Data to authenticate

        Returns:
            HMAC tag
        """
        if self.hmac_key is None:
            raise ValueError("HMAC key not established")

        h = HMAC.new(self.hmac_key, digestmod=SHA256)
        h.update(data)
        return h.digest()

    def verify_hmac(self, data: bytes, tag: bytes) -> bool:
        """
        Verify HMAC tag

        Args:
            data: Original data
            tag: HMAC tag to verify

        Returns:
            True if valid
        """
        if self.hmac_key is None:
            raise ValueError("HMAC key not established")

        h = HMAC.new(self.hmac_key, digestmod=SHA256)
        h.update(data)

        try:
            h.verify(tag)
            return True
        except ValueError:
            return False

    def create_secure_packet(self, payload: bytes) -> bytes:
        """
        Create fully secured packet: Encrypt + Sign + HMAC

        Format: [encrypted_packet] [hmac(32)] [signature(256)]
        (RSA-2048 signatures are always 256 bytes)

        Args:
            payload: Voice data to secure

        Returns:
            Fully secured packet
        """
        # Step 1: Encrypt payload
        encrypted = self.encrypt_packet(payload)

        # Step 2: Compute HMAC over encrypted data
        hmac_tag = self.compute_hmac(encrypted)

        # Step 3: Sign the entire package
        signature = self.sign_message(encrypted + hmac_tag)

        # Construct final packet (RSA-2048 signature is always 256 bytes)
        secure_packet = encrypted + hmac_tag + signature

        return secure_packet

    def verify_secure_packet(self, secure_packet: bytes) -> Optional[bytes]:
        """
        Verify and decrypt secure packet

        Args:
            secure_packet: Secured packet to verify

        Returns:
            Original payload or None if verification fails
        """
        try:
            # Parse packet structure
            # Format: [encrypted] [hmac(32)] [signature(256)]
            # RSA-2048 signatures are always 256 bytes

            signature = secure_packet[-256:]
            hmac_tag = secure_packet[-288:-256]
            encrypted = secure_packet[:-288]

            # Step 1: Verify signature (protects against imposter)
            if not self.verify_signature(encrypted + hmac_tag, signature):
                print("Signature verification failed - possible imposter!")
                return None

            # Step 2: Verify HMAC (protects against manipulation)
            if not self.verify_hmac(encrypted, hmac_tag):
                print("HMAC verification failed - content manipulated!")
                return None

            # Step 3: Decrypt (protects against eavesdropping)
            plaintext = self.decrypt_packet(encrypted)

            return plaintext

        except Exception as e:
            print(f"Packet verification error: {e}")
            return None


if __name__ == "__main__":
    print("Testing Cryptographic Module...")

    # Initialize two crypto modules (sender and receiver)
    sender = CryptoModule()
    receiver = CryptoModule()

    # Generate key pairs
    print("\n1. Generating RSA key pairs...")
    sender_priv, sender_pub = sender.generate_rsa_keypair()
    receiver_priv, receiver_pub = receiver.generate_rsa_keypair()

    # Exchange public keys
    print("2. Exchanging public keys...")
    sender.load_peer_public_key(receiver_pub)
    receiver.load_peer_public_key(sender_pub)

    # Sender generates and shares session keys
    print("3. Establishing session keys...")
    encrypted_keys = sender.generate_session_keys()
    receiver.receive_session_keys(encrypted_keys)

    # Test message
    test_message = b"This is a secret voice packet!"
    print(f"\n4. Original message: {test_message}")

    # Create secure packet
    print("5. Creating secure packet (Encrypt + HMAC + Sign)...")
    secure_packet = sender.create_secure_packet(test_message)
    print(f"   Secure packet size: {len(secure_packet)} bytes")

    # Verify and decrypt
    print("6. Verifying and decrypting packet...")
    decrypted = receiver.verify_secure_packet(secure_packet)

    if decrypted:
        print(f"   ✓ Decrypted message: {decrypted}")
        print(f"   ✓ Match: {decrypted == test_message}")
    else:
        print("   ✗ Verification failed!")

    # Test tampering detection
    print("\n7. Testing tampering detection...")
    tampered_packet = bytearray(secure_packet)
    tampered_packet[50] ^= 0xFF  # Flip some bits
    decrypted_tampered = receiver.verify_secure_packet(bytes(tampered_packet))
    print(f"   Tampered packet accepted: {decrypted_tampered is not None} (should be False)")

    print("\n✓ Cryptographic module tests complete!")
