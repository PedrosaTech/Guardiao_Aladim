"""
Campos customizados para LGPD e segurança.
"""
from django.db import models
from typing import Optional
from core.security.encryption import FieldEncryption


class EncryptedCharField(models.CharField):
    """
    Campo CharField que criptografa dados sensíveis automaticamente.
    
    Usa Fernet (symmetric encryption) para proteger dados como CPF, CNPJ, telefone, etc.
    A criptografia/descriptografia é transparente para o desenvolvedor.
    
    Compatibilidade:
    - Dados novos são automaticamente criptografados ao salvar
    - Dados antigos não criptografados continuam funcionando (fallback automático)
    - Ao ler, se não conseguir descriptografar, retorna o valor original
    
    Configuração:
    - Configure ENCRYPTION_KEY nas settings (variável de ambiente)
    - A chave deve ter no mínimo 32 caracteres ou será derivada via SHA256
    
    Exemplo:
        cpf = EncryptedCharField('CPF', max_length=18)
        cliente.cpf = '12345678900'  # Armazenado criptografado
        print(cliente.cpf)  # '12345678900' (descriptografado automaticamente)
    """
    
    def __init__(self, *args, **kwargs):
        # Aumenta max_length padrão para acomodar dados criptografados
        # (dados criptografados são ~33% maiores que o original)
        kwargs.setdefault('max_length', 500)
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value: Optional[str]) -> Optional[str]:
        """
        Prepara o valor antes de salvar no banco de dados.
        
        Criptografa o valor usando FieldEncryption antes de armazenar.
        Valores None ou vazios são mantidos como estão.
        
        Args:
            value: Valor a ser criptografado (pode ser None)
            
        Returns:
            Valor criptografado em string, ou None
        """
        if value is None:
            return None
        
        # Converte para string se necessário
        str_value = str(value) if value else ''
        
        # Se vazio, retorna como está
        if not str_value:
            return str_value
        
        # Criptografa o valor
        return FieldEncryption.encrypt(str_value)
    
    def from_db_value(self, value: Optional[str], expression, connection) -> Optional[str]:
        """
        Converte o valor do banco de dados para Python.
        
        Descriptografa automaticamente o valor ao ler do banco.
        Implementa fallback para compatibilidade com dados não criptografados:
        - Se não conseguir descriptografar, retorna o valor original
        - Permite migração gradual de dados existentes
        
        Args:
            value: Valor do banco (pode estar criptografado ou não)
            expression: Expressão SQL (usado pelo Django)
            connection: Conexão com banco (usado pelo Django)
            
        Returns:
            Valor descriptografado, ou o valor original se não puder descriptografar
        """
        if value is None:
            return None
        
        # Converte para string se necessário
        str_value = str(value) if value else ''
        
        # Se vazio, retorna como está
        if not str_value:
            return str_value
        
        # Tenta descriptografar (com fallback automático para dados antigos)
        return FieldEncryption.decrypt(str_value)

