"""
Key Generation Utility
Generates RSA key pairs for transmitter and receiver
"""

from crypto_module import CryptoModule
import argparse


def generate_keypair(prefix: str):
    """
    Generate and save RSA key pair

    Args:
        prefix: Prefix for key filenames (e.g., 'transmitter' or 'receiver')
    """
    print(f"\nGenerating {prefix} RSA key pair...")

    crypto = CryptoModule()
    private_key, public_key = crypto.generate_rsa_keypair(key_size=2048)

    # Save private key
    private_filename = f"{prefix}_private.pem"
    with open(private_filename, 'wb') as f:
        f.write(private_key)
    print(f"  ✓ Private key saved: {private_filename}")

    # Save public key
    public_filename = f"{prefix}_public.pem"
    with open(public_filename, 'wb') as f:
        f.write(public_key)
    print(f"  ✓ Public key saved: {public_filename}")

    return private_filename, public_filename


def main():
    parser = argparse.ArgumentParser(
        description='Generate RSA key pairs for secure voice transmission'
    )
    parser.add_argument('--transmitter', action='store_true',
                        help='Generate transmitter keys')
    parser.add_argument('--receiver', action='store_true',
                        help='Generate receiver keys')
    parser.add_argument('--both', action='store_true',
                        help='Generate both transmitter and receiver keys')

    args = parser.parse_args()

    print("=" * 60)
    print(" RSA Key Generation Utility")
    print("=" * 60)

    generated = []

    if args.both or (not args.transmitter and not args.receiver):
        # Generate both by default
        print("\nGenerating keys for both transmitter and receiver...")
        tx_files = generate_keypair('transmitter')
        rx_files = generate_keypair('receiver')
        generated.extend(tx_files)
        generated.extend(rx_files)

    else:
        if args.transmitter:
            tx_files = generate_keypair('transmitter')
            generated.extend(tx_files)

        if args.receiver:
            rx_files = generate_keypair('receiver')
            generated.extend(rx_files)

    print("\n" + "=" * 60)
    print(" Key Generation Complete!")
    print("=" * 60)
    print("\nGenerated files:")
    for filename in generated:
        print(f"  • {filename}")

    print("\n⚠ IMPORTANT: Keep private keys secure!")
    print("  • Never share private keys")
    print("  • Public keys can be freely shared")
    print("  • For actual deployment, exchange public keys securely")

    print("\nNext steps:")
    print("  1. Start receiver: python receiver.py --port 5000")
    print("  2. Start transmitter: python transmitter.py --host localhost --port 5000")


if __name__ == "__main__":
    main()
