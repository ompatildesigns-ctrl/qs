"""Token encryption/decryption utilities using Fernet."""
import os
from cryptography.fernet import Fernet


class TokenEncryptor:
    """Encrypts and decrypts OAuth tokens using Fernet symmetric encryption."""
    
    def __init__(self, encryption_key: str):
        """Initialize with base64-encoded encryption key."""
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt(self, token: str) -> str:
        """Encrypt a token string and return base64-encoded ciphertext."""
        encrypted = self.cipher.encrypt(token.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt a base64-encoded ciphertext and return the original token."""
        decrypted = self.cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()


# Singleton instance
_encryptor = None


def get_encryptor() -> TokenEncryptor:
    """Get or create the singleton encryptor instance."""
    global _encryptor
    if _encryptor is None:
        encryption_key = os.environ.get('JIRA_ENC_KEY')
        if not encryption_key:
            raise ValueError("JIRA_ENC_KEY environment variable not set")
        _encryptor = TokenEncryptor(encryption_key)
    return _encryptor
