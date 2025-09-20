# secure_comm.py
# This module handles the encryption and decryption of simple string messages.

from cryptography.fernet import Fernet

class SecureChannel:
    """
    A class to handle symmetric encryption and decryption of string messages using a shared key.
    """
    def __init__(self, key: bytes):
        """
        Initializes the channel with a secret key.
        """
        self.cipher_suite = Fernet(key)

    @staticmethod
    def generate_key() -> bytes:
        """
        Generates a new, secure key. Must be shared securely.
        """
        return Fernet.generate_key()

    def encrypt_message(self, plain_text_message: str) -> bytes:
        """
        Encrypts a plain string message.

        Args:
            plain_text_message (str): The alert string to encrypt.

        Returns:
            bytes: The encrypted message token.
        """
        message_bytes = plain_text_message.encode('utf-8')
        encrypted_message = self.cipher_suite.encrypt(message_bytes)
        return encrypted_message

    def decrypt_message(self, encrypted_token: bytes) -> str:
        """
        Decrypts a message token back into a string.

        Args:
            encrypted_token (bytes): The encrypted message to decrypt.

        Returns:
            str: The original, decrypted alert string. Returns None on failure.
        """
        try:
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_token)
            decrypted_message = decrypted_bytes.decode('utf-8')
            return decrypted_message
        except Exception as e:
            print(f"Decryption failed! Error: {e}")
            return None
