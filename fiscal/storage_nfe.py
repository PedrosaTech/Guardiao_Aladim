"""
Armazenamento temporário de XML de NF-e para importação.

Evita guardar XML inteiro na sessão (limite ~4KB). NF-e pode ter até 990 itens.
"""
import uuid
from pathlib import Path

from django.conf import settings


def get_tmp_dir() -> Path:
    """Retorna o diretório de arquivos temporários de NF-e."""
    tmp_dir = getattr(settings, 'NFE_IMPORT_TMP_DIR', None)
    if not tmp_dir:
        tmp_dir = Path(settings.MEDIA_ROOT) / 'tmp' / 'nfe_import'
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def salvar_xml_temporario(xml_content: str) -> str:
    """
    Salva o XML em arquivo temporário e retorna a chave (UUID) para a sessão.

    Returns:
        str: UUID do arquivo (chave para recuperar depois)
    """
    key = str(uuid.uuid4())
    tmp_dir = get_tmp_dir()
    path = tmp_dir / f"{key}.xml"
    path.write_text(xml_content, encoding='utf-8')
    return key


def carregar_xml_temporario(key: str) -> str:
    """
    Carrega o XML do arquivo temporário pela chave.

    Returns:
        str: Conteúdo do XML

    Raises:
        FileNotFoundError: se o arquivo não existir
    """
    tmp_dir = get_tmp_dir()
    path = tmp_dir / f"{key}.xml"
    if not path.exists():
        raise FileNotFoundError(f"Arquivo temporário não encontrado: {key}")
    return path.read_text(encoding='utf-8')


def deletar_xml_temporario(key: str) -> bool:
    """
    Deleta o arquivo temporário após confirmação bem-sucedida.

    Returns:
        bool: True se deletou, False se não existia
    """
    tmp_dir = get_tmp_dir()
    path = tmp_dir / f"{key}.xml"
    if path.exists():
        path.unlink()
        return True
    return False


def limpar_xml_temporarios_antigos(horas: int = 24) -> int:
    """
    Remove arquivos XML temporários com mais de N horas.
    Cobre abandono (usuário fechou aba sem confirmar).

    Returns:
        int: Quantidade de arquivos removidos
    """
    import time

    tmp_dir = get_tmp_dir()
    if not tmp_dir.exists():
        return 0

    limite = time.time() - (horas * 3600)
    removidos = 0
    for path in tmp_dir.glob("*.xml"):
        try:
            if path.stat().st_mtime < limite:
                path.unlink()
                removidos += 1
        except OSError:
            pass
    return removidos
