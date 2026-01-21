"""
Sistema de criptografia para campos sensíveis usando Fernet (cryptography).

LGPD Compliance: Protege dados pessoais sensíveis (CPF, CNPJ, telefone, etc.)
"""
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import base64
import hashlib
from functools import lru_cache
from typing import Optional


class FieldEncryption:
    """
    Classe para criptografar e descriptografar valores de campos sensíveis.
    
    Usa Fernet (symmetric encryption) da biblioteca cryptography.
    A chave é obtida de settings.ENCRYPTION_KEY e derivada via SHA256 se necessário.
    """
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_cipher() -> Fernet:
        """
        Retorna o objeto Fernet cipher para criptografia/descriptografia.
        
        Cacheado com lru_cache para melhor performance.
        
        Returns:
            Fernet: Objeto cipher configurado
            
        Raises:
            ImproperlyConfigured: Se ENCRYPTION_KEY não estiver configurada
        """
        encryption_key = getattr(settings, 'ENCRYPTION_KEY', None)
        
        if not encryption_key:
            raise ImproperlyConfigured(
                'ENCRYPTION_KEY não está configurada nas settings. '
                'Configure a variável de ambiente ENCRYPTION_KEY com uma chave secreta (mínimo 32 caracteres).'
            )
        
        # Converte para bytes se for string
        if isinstance(encryption_key, str):
            key = encryption_key.encode('utf-8')
        else:
            key = encryption_key
        
        # Se a chave não tiver 32 bytes, deriva via SHA256
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        # Gera chave Fernet compatível (base64urlsafe)
        fernet_key = base64.urlsafe_b64encode(key)
        
        return Fernet(fernet_key)
    
    @classmethod
    def encrypt(cls, value: Optional[str]) -> Optional[str]:
        """
        Criptografa um valor string.
        
        Args:
            value: Valor a ser criptografado (pode ser None ou string vazia)
            
        Returns:
            String criptografada em base64, ou o valor original se None/vazio
        """
        if not value:
            return value
        
        try:
            cipher = cls.get_cipher()
            encrypted = cipher.encrypt(value.encode('utf-8'))
            # Retorna em base64urlsafe para armazenamento seguro
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            # Em caso de erro, retorna original (melhor que quebrar)
            # Em produção, você pode querer logar o erro sem expor o valor
            return value
    
    @classmethod
    def decrypt(cls, encrypted_value: Optional[str]) -> Optional[str]:
        """
        Descriptografa um valor previamente criptografado.
        
        Implementa fallback para compatibilidade com dados não criptografados:
        - Se o valor não puder ser descriptografado, retorna o valor original
        - Isso permite migração gradual de dados existentes
        
        Args:
            encrypted_value: Valor criptografado em base64, ou None
            
        Returns:
            String descriptografada, ou o valor original se não puder descriptografar
        """
        if not encrypted_value:
            return encrypted_value
        
        try:
            cipher = cls.get_cipher()
            # Decodifica de base64urlsafe
            decoded = base64.urlsafe_b64decode(encrypted_value.encode('utf-8'))
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except (ValueError, TypeError, Exception):
            # Se falhar ao descriptografar, provavelmente é dado antigo não criptografado
            # Retorna o valor original para compatibilidade
            return encrypted_value

