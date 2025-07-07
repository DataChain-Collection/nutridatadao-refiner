import warnings

from cryptography.utils import CryptographyDeprecationWarning

# Suppress CryptographyDeprecationWarning from pgpy internals
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

import pgpy
from pgpy.constants import CompressionAlgorithm, HashAlgorithm, SymmetricKeyAlgorithm
import os
from refiner.config import settings


def encrypt_file(encryption_key: str, file_path: str, output_path: str = None) -> str:
    """Symmetrically encrypts a file with AES-256 using a passphrase.

    Args:
        encryption_key: Passphrase for encryption
        file_path: Path to file to encrypt
        output_path: Output path (defaults to file_path + .pgp)

    Returns:
        Path to encrypted file
    """
    output_path = output_path or f"{file_path}.pgp"

    with open(file_path, 'rb') as f:
        buffer = f.read()

    # Create message with ZLIB compression
    message = pgpy.PGPMessage.new(buffer, compression=CompressionAlgorithm.ZLIB)

    # Encrypt with AES-256 and SHA512 hash
    encrypted_message = message.encrypt(
        passphrase=encryption_key,
        hash=HashAlgorithm.SHA512,
        symmetric=SymmetricKeyAlgorithm.AES256
    )

    with open(output_path, 'wb') as f:
        f.write(str(encrypted_message).encode())

    return output_path


def decrypt_file(encryption_key: str, file_path: str, output_path: str = None) -> str:
    """Symmetrically decrypts a PGP-encrypted file.

    Args:
        encryption_key: Passphrase used for encryption
        file_path: Path to encrypted file
        output_path: Output path (default removes .pgp extension)

    Returns:
        Path to decrypted file
    """
    if not output_path:
        base_path = file_path.rsplit('.pgp', 1)[0]
        output_path = f"{base_path}.decrypted"

    with open(file_path, 'rb') as f:
        encrypted_data = f.read()

    message = pgpy.PGPMessage.from_blob(encrypted_data)
    decrypted_message = message.decrypt(encryption_key)

    with open(output_path, 'wb') as f:
        f.write(decrypted_message.message)

    return output_path


# Test with: python -m refiner.utils.encrypt
if __name__ == "__main__":    
    plaintext_db = os.path.join(settings.OUTPUT_DIR, "db.libsql")

    # Encrypt and decrypt
    encrypted_path = encrypt_file(settings.REFINEMENT_ENCRYPTION_KEY, plaintext_db)
    print(f"File encrypted to: {encrypted_path}")

    decrypted_path = decrypt_file(settings.REFINEMENT_ENCRYPTION_KEY, encrypted_path)
    print(f"File decrypted to: {decrypted_path}")
