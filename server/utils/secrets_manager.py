"""
Secrets Management System
==========================
Secure encryption and storage of sensitive credentials.

Author: Claude Code
Date: 2025-11-11
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from typing import Optional
from utils.logger import app_logger


class SecretsManager:
    """
    Manage encryption and decryption of sensitive data.
    Uses Fernet (symmetric encryption) with user-specific keys.
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize secrets manager.

        Args:
            master_key: Master encryption key (from environment)
        """
        self.master_key = master_key or os.getenv('SECRETS_MASTER_KEY')

        if not self.master_key:
            raise ValueError(
                "SECRETS_MASTER_KEY environment variable must be set. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

    def _derive_key(self, user_id: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """
        Derive encryption key from master key and user ID.

        Args:
            user_id: User identifier
            salt: Optional salt (generates new if not provided)

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(
            kdf.derive(f"{self.master_key}:{user_id}".encode())
        )

        return key, salt

    def encrypt_github_token(self, token: str, user_id: str) -> dict:
        """
        Encrypt GitHub token for storage.

        Args:
            token: GitHub personal access token
            user_id: User identifier

        Returns:
            Dictionary with encrypted_token and salt
        """
        app_logger.info(
            "Encrypting GitHub token",
            user_id=user_id,
            event="token_encrypt"
        )

        try:
            # Derive user-specific key
            key, salt = self._derive_key(user_id)

            # Encrypt token
            f = Fernet(key)
            encrypted_token = f.encrypt(token.encode())

            # Encode for storage
            encrypted_b64 = base64.b64encode(encrypted_token).decode()
            salt_b64 = base64.b64encode(salt).decode()

            app_logger.info(
                "GitHub token encrypted successfully",
                user_id=user_id,
                event="token_encrypt_success"
            )

            return {
                'encrypted_token': encrypted_b64,
                'salt': salt_b64
            }

        except Exception as e:
            app_logger.error(
                "Failed to encrypt GitHub token",
                user_id=user_id,
                error=str(e),
                event="token_encrypt_error"
            )
            raise

    def decrypt_github_token(self, encrypted_data: dict, user_id: str) -> str:
        """
        Decrypt GitHub token from storage.

        Args:
            encrypted_data: Dictionary with encrypted_token and salt
            user_id: User identifier

        Returns:
            Decrypted GitHub token
        """
        app_logger.info(
            "Decrypting GitHub token",
            user_id=user_id,
            event="token_decrypt"
        )

        try:
            # Decode from storage
            encrypted_token = base64.b64decode(encrypted_data['encrypted_token'])
            salt = base64.b64decode(encrypted_data['salt'])

            # Derive same key
            key, _ = self._derive_key(user_id, salt=salt)

            # Decrypt token
            f = Fernet(key)
            decrypted_token = f.decrypt(encrypted_token).decode()

            app_logger.info(
                "GitHub token decrypted successfully",
                user_id=user_id,
                event="token_decrypt_success"
            )

            return decrypted_token

        except Exception as e:
            app_logger.error(
                "Failed to decrypt GitHub token",
                user_id=user_id,
                error=str(e),
                event="token_decrypt_error"
            )
            raise

    def encrypt_api_key(self, api_key: str, service: str, user_id: str) -> dict:
        """
        Encrypt API key for any service.

        Args:
            api_key: API key to encrypt
            service: Service name (e.g., 'anthropic', 'openai')
            user_id: User identifier

        Returns:
            Dictionary with encrypted_key and metadata
        """
        app_logger.info(
            f"Encrypting {service} API key",
            user_id=user_id,
            service=service,
            event="api_key_encrypt"
        )

        key, salt = self._derive_key(user_id)
        f = Fernet(key)
        encrypted_key = f.encrypt(api_key.encode())

        return {
            'encrypted_key': base64.b64encode(encrypted_key).decode(),
            'salt': base64.b64encode(salt).decode(),
            'service': service
        }

    def decrypt_api_key(self, encrypted_data: dict, user_id: str) -> str:
        """
        Decrypt API key.

        Args:
            encrypted_data: Dictionary with encrypted_key and salt
            user_id: User identifier

        Returns:
            Decrypted API key
        """
        encrypted_key = base64.b64decode(encrypted_data['encrypted_key'])
        salt = base64.b64decode(encrypted_data['salt'])

        key, _ = self._derive_key(user_id, salt=salt)
        f = Fernet(key)

        return f.decrypt(encrypted_key).decode()


# Global secrets manager instance
secrets_manager = SecretsManager()


if __name__ == "__main__":
    # Test secrets manager
    print("=" * 60)
    print("Secrets Manager Test")
    print("=" * 60)

    # Set test master key
    os.environ['SECRETS_MASTER_KEY'] = Fernet.generate_key().decode()

    manager = SecretsManager()
    test_user = "test-user-123"
    test_token = "ghp_test123456789"

    # Encrypt
    print("\n1. Encrypting GitHub token...")
    encrypted = manager.encrypt_github_token(test_token, test_user)
    print(f"Encrypted: {encrypted['encrypted_token'][:50]}...")
    print(f"Salt: {encrypted['salt'][:30]}...")

    # Decrypt
    print("\n2. Decrypting GitHub token...")
    decrypted = manager.decrypt_github_token(encrypted, test_user)
    print(f"Decrypted: {decrypted}")

    # Verify
    print("\n3. Verification...")
    if decrypted == test_token:
        print("✅ Encryption/decryption successful!")
    else:
        print("❌ Encryption/decryption failed!")

    print("\n" + "=" * 60)
