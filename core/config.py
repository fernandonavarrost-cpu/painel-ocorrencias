from pathlib import Path
import socket

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados"

CADASTRO_XLSX = DADOS_DIR / "cadastro.xlsx"
OCORRENCIAS_XLSX = DADOS_DIR / "ocorrencias.xlsx"
AVISOS_XLSX = DADOS_DIR / "avisos.xlsx"

SHEET_ALUNOS = "Alunos"
SHEET_PROFESSORES = "Professores"
SHEET_DADOS = "Dados"

COLUNAS_ALUNOS = ["Serie", "Aluno"]
COLUNAS_PROFESSORES = ["Professor"]
COLUNAS_OCORRENCIAS = [
    "ID", "Data", "Serie", "Aluno", "Professor", "Descricao", "Status", "Criado_em"
]
COLUNAS_AVISOS = [
    "ID", "Data", "Serie", "Aluno", "Professor", "Tipos", "Status", "Criado_em"
]

TIPOS_AVISO = [
    "Fora da sala",
    "Agressão física",
    "Dano ao patrimônio",
    "Desacato",
]

STATUS_PENDENTE = "Pendente"
STATUS_LIDO = "Lido"

def _senha_gestor() -> str:
    """Senha do painel do gestor: st.secrets na nuvem, fallback local."""
    try:
        return str(st.secrets["SENHA_GESTOR"])
    except Exception:
        return "gestoratento"


SENHA_GESTOR = _senha_gestor()

AUTO_REFRESH_SEGUNDOS = 10
MAX_ALERTAS_LISTA = 30

PLACEHOLDER = "-- Selecione --"


def ip_local() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def url_local(porta: int = 8501) -> str:
    return f"http://{ip_local()}:{porta}"
