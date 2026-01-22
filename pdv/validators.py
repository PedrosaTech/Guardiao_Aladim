"""
Validadores para módulo PDV - Validações de Pirotecnia.
"""
import re
from datetime import date
from django.core.exceptions import ValidationError


def validar_cpf(cpf):
    """
    Valida CPF usando algoritmo oficial da Receita Federal.
    
    Remove formatação e valida os dígitos verificadores.
    
    Args:
        cpf: CPF com ou sem formatação (ex: "123.456.789-00" ou "12345678900")
    
    Returns:
        str: CPF limpo (apenas números)
    
    Raises:
        ValidationError: Se CPF for inválido
    """
    # Remove formatação
    cpf_limpo = re.sub(r'[^0-9]', '', str(cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf_limpo) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    
    # Verifica se todos os dígitos são iguais (CPFs inválidos conhecidos)
    if cpf_limpo == cpf_limpo[0] * 11:
        raise ValidationError('CPF inválido')
    
    # Valida primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf_limpo[i]) * (10 - i)
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[9]) != digito1:
        raise ValidationError('CPF inválido - dígito verificador incorreto')
    
    # Valida segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf_limpo[i]) * (11 - i)
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_limpo[10]) != digito2:
        raise ValidationError('CPF inválido - dígito verificador incorreto')
    
    return cpf_limpo


def formatar_cpf(cpf):
    """
    Formata CPF para exibição: 000.000.000-00
    
    Args:
        cpf: CPF com ou sem formatação
    
    Returns:
        str: CPF formatado
    """
    cpf_limpo = re.sub(r'[^0-9]', '', str(cpf))
    if len(cpf_limpo) == 11:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    return cpf_limpo


def calcular_idade(data_nascimento):
    """
    Calcula idade a partir da data de nascimento.
    
    Args:
        data_nascimento: datetime.date
    
    Returns:
        int: Idade em anos
    """
    hoje = date.today()
    idade = hoje.year - data_nascimento.year
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade


def validar_idade_minima(data_nascimento, idade_minima=18):
    """
    Valida se a pessoa tem idade mínima necessária.
    
    Args:
        data_nascimento: datetime.date
        idade_minima: int (padrão 18)
    
    Returns:
        bool: True se maior ou igual à idade mínima
    
    Raises:
        ValidationError: Se menor de idade
    """
    idade = calcular_idade(data_nascimento)
    if idade < idade_minima:
        raise ValidationError(
            f'Idade mínima de {idade_minima} anos não atingida. '
            f'Idade atual: {idade} anos.'
        )
    return True







