from cryptography.fernet import Fernet
import os

# Path to the file where the encryption key is stored
KEY_FILE = ".encryption_key"


def generate_key():
    """Generates a new encryption key and saves it to the key file."""
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
    return key


def load_key():
    """Loads the encryption key from the key file, or generates a new one if it doesn't exist."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        return generate_key()


class EncryptedStore:
    """Handles encryption and decryption of data."""

    def __init__(self):
        self.key = load_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> bytes:
        """Encrypts a string."""
        return self.fernet.encrypt(data.encode("utf-8"))

    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypts an encrypted string."""
        return self.fernet.decrypt(encrypted_data).decode("utf-8")


# Global instance of the encrypted store
encrypted_store = EncryptedStore()
