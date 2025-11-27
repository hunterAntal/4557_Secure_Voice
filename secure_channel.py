"""
Secure Channel Protocol
Manages secure communication sessions with handshake and key exchange
"""

import socket
import struct
import time
from enum import Enum
from typing import Optional, Tuple, Callable
from crypto_module import CryptoModule
from error_correction import ErrorCorrection
import json


class MessageType(Enum):
    """Message types for protocol"""
    HELLO = 0x01           # Initial handshake
    KEY_EXCHANGE = 0x02    # Session key exchange
    CHALLENGE = 0x03       # Challenge-response authentication
    RESPONSE = 0x04        # Challenge response
    DATA = 0x05            # Encrypted voice data
    ACK = 0x06            # Acknowledgment
    HEARTBEAT = 0x07      # Keep-alive
    GOODBYE = 0x08        # Session termination


class SecureChannel:
    """
    Implements secure communication channel with:
    - Mutual authentication
    - Key exchange
    - Encrypted data transfer
    - Error correction
    """

    def __init__(self, private_key_pem: bytes, public_key_pem: bytes):
        """
        Initialize secure channel

        Args:
            private_key_pem: Own RSA private key
            public_key_pem: Own RSA public key
        """
        self.crypto = CryptoModule()
        self.crypto.load_private_key(private_key_pem)
        self.public_key = public_key_pem

        self.error_correction = ErrorCorrection(nsym=32)

        self.socket = None
        self.peer_address = None
        self.is_authenticated = False
        self.session_active = False

        # Statistics
        self.packets_sent = 0
        self.packets_received = 0
        self.errors_corrected = 0

    def create_packet(self, msg_type: MessageType, payload: bytes) -> bytes:
        """
        Create protocol packet

        Format: [type(1)] [length(4)] [payload]

        Args:
            msg_type: Message type
            payload: Payload data

        Returns:
            Complete packet
        """
        header = struct.pack('!BI', msg_type.value, len(payload))
        return header + payload

    def parse_packet(self, packet: bytes) -> Tuple[MessageType, bytes]:
        """
        Parse protocol packet

        Args:
            packet: Raw packet

        Returns:
            Tuple of (message_type, payload)
        """
        msg_type_val, payload_len = struct.unpack('!BI', packet[:5])
        msg_type = MessageType(msg_type_val)
        payload = packet[5:5 + payload_len]
        return msg_type, payload

    def handshake_initiator(self, sock: socket.socket, peer_addr: Tuple[str, int]) -> bool:
        """
        Initiate secure handshake (client side)

        Steps:
        1. Send HELLO with public key
        2. Receive peer's HELLO
        3. Send KEY_EXCHANGE with session keys
        4. Authenticate with challenge-response
        5. Receive ACK

        Args:
            sock: Socket connection
            peer_addr: Peer address (host, port)

        Returns:
            True if handshake successful
        """
        self.socket = sock
        self.peer_address = peer_addr

        try:
            # Step 1: Send HELLO with public key
            print("[Client] Sending HELLO...")
            hello_payload = json.dumps({
                'version': '1.0',
                'public_key': self.public_key.decode('utf-8'),
                'timestamp': time.time()
            }).encode()

            hello_packet = self.create_packet(MessageType.HELLO, hello_payload)
            sock.sendto(hello_packet, peer_addr)

            # Step 2: Receive peer's HELLO
            print("[Client] Waiting for server HELLO...")
            data, addr = sock.recvfrom(65536)
            msg_type, payload = self.parse_packet(data)

            if msg_type != MessageType.HELLO:
                print(f"[Client] Expected HELLO, got {msg_type}")
                return False

            peer_hello = json.loads(payload.decode())
            peer_public_key = peer_hello['public_key'].encode()
            self.crypto.load_peer_public_key(peer_public_key)
            print("[Client] Received peer public key")

            # Step 3: Generate and send session keys
            print("[Client] Generating session keys...")
            encrypted_keys = self.crypto.generate_session_keys()

            key_packet = self.create_packet(MessageType.KEY_EXCHANGE, encrypted_keys)
            sock.sendto(key_packet, peer_addr)

            # Step 4: Challenge-response authentication
            print("[Client] Waiting for challenge...")
            data, addr = sock.recvfrom(65536)
            msg_type, challenge = self.parse_packet(data)

            if msg_type != MessageType.CHALLENGE:
                print(f"[Client] Expected CHALLENGE, got {msg_type}")
                return False

            # Sign challenge
            signature = self.crypto.sign_message(challenge)
            response_packet = self.create_packet(MessageType.RESPONSE, signature)
            sock.sendto(response_packet, peer_addr)

            # Step 5: Wait for ACK
            print("[Client] Waiting for ACK...")
            data, addr = sock.recvfrom(65536)
            msg_type, _ = self.parse_packet(data)

            if msg_type != MessageType.ACK:
                print(f"[Client] Expected ACK, got {msg_type}")
                return False

            self.is_authenticated = True
            self.session_active = True
            print("[Client] Handshake complete - session established")
            return True

        except Exception as e:
            print(f"[Client] Handshake failed: {e}")
            return False

    def handshake_responder(self, sock: socket.socket) -> bool:
        """
        Respond to secure handshake (server side)

        Args:
            sock: Socket connection

        Returns:
            True if handshake successful
        """
        self.socket = sock

        try:
            # Step 1: Receive HELLO
            print("[Server] Waiting for client HELLO...")
            data, addr = sock.recvfrom(65536)
            self.peer_address = addr

            msg_type, payload = self.parse_packet(data)

            if msg_type != MessageType.HELLO:
                print(f"[Server] Expected HELLO, got {msg_type}")
                return False

            peer_hello = json.loads(payload.decode())
            peer_public_key = peer_hello['public_key'].encode()
            self.crypto.load_peer_public_key(peer_public_key)
            print(f"[Server] Received HELLO from {addr}")

            # Step 2: Send our HELLO
            print("[Server] Sending HELLO...")
            hello_payload = json.dumps({
                'version': '1.0',
                'public_key': self.public_key.decode('utf-8'),
                'timestamp': time.time()
            }).encode()

            hello_packet = self.create_packet(MessageType.HELLO, hello_payload)
            sock.sendto(hello_packet, addr)

            # Step 3: Receive session keys
            print("[Server] Waiting for session keys...")
            data, addr = sock.recvfrom(65536)
            msg_type, encrypted_keys = self.parse_packet(data)

            if msg_type != MessageType.KEY_EXCHANGE:
                print(f"[Server] Expected KEY_EXCHANGE, got {msg_type}")
                return False

            # Decrypt session keys
            if not self.crypto.receive_session_keys(encrypted_keys):
                print("[Server] Failed to receive session keys")
                return False
            print("[Server] Session keys established")

            # Step 4: Send challenge for authentication
            print("[Server] Sending challenge...")
            challenge = self.crypto.session_key  # Use session key as challenge
            challenge_packet = self.create_packet(MessageType.CHALLENGE, challenge)
            sock.sendto(challenge_packet, addr)

            # Step 5: Verify response
            print("[Server] Waiting for response...")
            data, addr = sock.recvfrom(65536)
            msg_type, signature = self.parse_packet(data)

            if msg_type != MessageType.RESPONSE:
                print(f"[Server] Expected RESPONSE, got {msg_type}")
                return False

            # Verify signature
            if not self.crypto.verify_signature(challenge, signature):
                print("[Server] Authentication failed - invalid signature")
                return False

            print("[Server] Authentication successful")

            # Step 6: Send ACK
            ack_packet = self.create_packet(MessageType.ACK, b'OK')
            sock.sendto(ack_packet, addr)

            self.is_authenticated = True
            self.session_active = True
            print("[Server] Handshake complete - session established")
            return True

        except Exception as e:
            print(f"[Server] Handshake failed: {e}")
            return False

    def send_data(self, data: bytes) -> bool:
        """
        Send encrypted and error-corrected data

        Args:
            data: Plaintext data

        Returns:
            True if sent successfully
        """
        if not self.session_active:
            print("Session not active")
            return False

        try:
            # Step 1: Apply error correction
            ec_data = self.error_correction.encode(data)

            # Step 2: Encrypt and authenticate
            secure_packet = self.crypto.create_secure_packet(ec_data)

            # Step 3: Create protocol packet
            data_packet = self.create_packet(MessageType.DATA, secure_packet)

            # Step 4: Send
            self.socket.sendto(data_packet, self.peer_address)
            self.packets_sent += 1

            return True

        except Exception as e:
            print(f"Send error: {e}")
            return False

    def receive_data(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        Receive and decrypt data

        Args:
            timeout: Receive timeout in seconds

        Returns:
            Decrypted data or None
        """
        if not self.session_active:
            print("Session not active")
            return None

        try:
            # Set timeout
            self.socket.settimeout(timeout)

            # Receive packet
            data, addr = self.socket.recvfrom(65536)

            # Parse packet
            msg_type, payload = self.parse_packet(data)

            if msg_type != MessageType.DATA:
                print(f"Expected DATA, got {msg_type}")
                return None

            # Verify and decrypt
            ec_data = self.crypto.verify_secure_packet(payload)

            if ec_data is None:
                print("Packet verification failed")
                return None

            # Error correction
            plaintext, errors = self.error_correction.decode(ec_data)

            if errors >= 0:
                self.errors_corrected += errors

            self.packets_received += 1

            return plaintext

        except socket.timeout:
            return None
        except Exception as e:
            print(f"Receive error: {e}")
            return None

    def close(self):
        """Close secure session"""
        if self.session_active and self.socket:
            try:
                # Send goodbye
                goodbye_packet = self.create_packet(MessageType.GOODBYE, b'')
                self.socket.sendto(goodbye_packet, self.peer_address)
            except:
                pass

        self.session_active = False
        self.is_authenticated = False
        print(f"\nSession statistics:")
        print(f"  Packets sent: {self.packets_sent}")
        print(f"  Packets received: {self.packets_received}")
        print(f"  Errors corrected: {self.errors_corrected}")

    def get_statistics(self) -> dict:
        """Get channel statistics"""
        return {
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'errors_corrected': self.errors_corrected,
            'session_active': self.session_active,
            'authenticated': self.is_authenticated
        }


if __name__ == "__main__":
    print("Secure Channel Protocol")
    print("Run transmitter.py and receiver.py for full test")
