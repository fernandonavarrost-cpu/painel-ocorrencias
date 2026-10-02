import os
import threading
import time
from contextlib import contextmanager
from datetime import date

import pandas as pd

from . import config

try:
    import msvcrt
except ImportError:  # non-Windows
    msvcrt = None
    import fcntl

_THREAD_LOCK = threading.RLock()


@contextmanager
def _lock(path, timeout: float = 15.0):
    """Trava o arquivo entre threads e processos (Windows/Unix)."""
    lock_path = f"{path}.lock"
    with _THREAD_LOCK:
        if not os.path.exists(lock_path):
            try:
                with open(lock_path, "wb") as fh:
                    fh.write(b"0")
            except OSError:
                pass
        fh = open(lock_path, "r+b")
        try:
            deadline = time.time() + timeout
            while True:
                try:
                    if msvcrt:
                        fh.seek(0)
                        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.time() > deadline:
                        raise TimeoutError(f"Não foi possível travar {path}")
                    time.sleep(0.05)
            yield
        finally:
            try:
                if msvcrt:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fh, fcntl.LOCK_UN)
            except OSError:
                pass
            fh.close()


def _sheet_existe(path, sheet_name: str) -> bool:
    if not path.exists():
        return False
    try:
        return sheet_name in pd.ExcelFile(path).sheet_names
    except (ValueError, OSError):
        return False


def _ler(path, colunas, sheet_name: str) -> pd.DataFrame:
    """Leitura sem trava (usar apenas com a trava já adquirida)."""
    if not path.exists() or not _sheet_existe(path, sheet_name):
        return pd.DataFrame(columns=colunas)
    try:
        df = pd.read_excel(path, sheet_name=sheet_name)
    except (ValueError, OSError):
        return pd.DataFrame(columns=colunas)
    for col in colunas:
        if col not in df.columns:
            df[col] = pd.NA
    return df[colunas].copy()


def ler_planilha(path, colunas, sheet_name: str = config.SHEET_DADOS) -> pd.DataFrame:
    """Lê uma planilha; retorna DataFrame vazio (com as colunas) se não existir."""
    if not path.exists():
        return pd.DataFrame(columns=colunas)
    with _lock(path):
        return _ler(path, colunas, sheet_name)


def _salvar(path, df: pd.DataFrame, sheet_name: str = config.SHEET_DADOS):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False, sheet_name=sheet_name)


def _escrever_sheet(path, df: pd.DataFrame, sheet_name: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with pd.ExcelWriter(path, engine="openpyxl", mode="a",
                            if_sheet_exists="replace") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    else:
        with pd.ExcelWriter(path, engine="openpyxl", mode="w") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)


def garantir_planilha(path, colunas, sheet_name: str = config.SHEET_DADOS):
    """Cria o arquivo com cabeçalho caso ainda não existir."""
    if _sheet_existe(path, sheet_name):
        return
    with _lock(path):
        if _sheet_existe(path, sheet_name):
            return
        _salvar(path, pd.DataFrame(columns=colunas), sheet_name)


def _proximo_id(df: pd.DataFrame) -> int:
    if df.empty or "ID" not in df.columns:
        return 1
    ids = pd.to_numeric(df["ID"], errors="coerce").dropna()
    return int(ids.max()) + 1 if not ids.empty else 1


def adicionar_linha(path, linha: dict, colunas,
                    sheet_name: str = config.SHEET_DADOS) -> int:
    """Acrescenta uma linha (append) e devolve o ID gerado."""
    with _lock(path):
        df = _ler(path, colunas, sheet_name)
        novo_id = _proximo_id(df)
        nova = pd.DataFrame([{**{c: pd.NA for c in colunas}, **linha, "ID": novo_id}])
        df = pd.concat([df[nova.columns], nova], ignore_index=True)
        _salvar(path, df, sheet_name)
    return novo_id


def atualizar_status(path, registro_id, novo_status: str, colunas,
                     sheet_name: str = config.SHEET_DADOS) -> bool:
    with _lock(path):
        df = _ler(path, colunas, sheet_name)
        if df.empty:
            return False
        alvo = pd.to_numeric(df["ID"], errors="coerce")
        mascara = alvo == pd.to_numeric(registro_id, errors="coerce")
        if not mascara.any():
            return False
        df.loc[mascara, "Status"] = novo_status
        _salvar(path, df, sheet_name)
    return True


def normalizar_data(valor) -> date | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    ts = pd.to_datetime(valor, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.date()


def formatar_data(valor) -> str:
    d = normalizar_data(valor)
    return d.strftime("%d/%m/%Y") if d else "-"


_COLUNAS_ALERTAS = ["ID", "Data", "Serie", "Aluno", "Professor",
                    "Detalhe", "Status", "Criado_em", "Registro", "Arquivo"]


def carregar_alertas() -> pd.DataFrame:
    """Unifica ocorrências e avisos para a página do gestor."""
    oc = ler_planilha(config.OCORRENCIAS_XLSX, config.COLUNAS_OCORRENCIAS)
    av = ler_planilha(config.AVISOS_XLSX, config.COLUNAS_AVISOS)

    if not oc.empty:
        oc = oc.rename(columns={"Descricao": "Detalhe"})
        oc["Registro"] = "Ocorrência"
        oc["Arquivo"] = "ocorrencias"
    else:
        oc = pd.DataFrame(columns=_COLUNAS_ALERTAS)

    if not av.empty:
        av = av.rename(columns={"Tipos": "Detalhe"})
        av["Registro"] = "Aviso"
        av["Arquivo"] = "avisos"
    else:
        av = pd.DataFrame(columns=_COLUNAS_ALERTAS)

    df = pd.concat([av, oc], ignore_index=True)
    if df.empty:
        return df
    df["_ordem"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0)
    df["_data_ord"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.sort_values(["_data_ord", "_ordem"], ascending=[False, False])
    return df.drop(columns=["_ordem", "_data_ord"]).reset_index(drop=True)


def atualizar_alerta(arquivo: str, registro_id, novo_status: str) -> bool:
    if arquivo == "avisos":
        return atualizar_status(config.AVISOS_XLSX, registro_id, novo_status,
                                config.COLUNAS_AVISOS)
    return atualizar_status(config.OCORRENCIAS_XLSX, registro_id, novo_status,
                            config.COLUNAS_OCORRENCIAS)


def _dados_alunos_exemplo() -> pd.DataFrame:
    return pd.DataFrame({
        "Serie": ["1º Ano A"] * 3 + ["2º Ano B"] * 3 + ["3º Ano A"] * 2,
        "Aluno": [
            "Ana Beatriz Souza", "Carlos Eduardo Lima", "Mariana Oliveira",
            "Pedro Henrique Santos", "Juliana Ferreira", "Lucas Ramos",
            "Gabriel Almeida", "Isabela Costa",
        ],
    })


def _dados_professores_exemplo() -> pd.DataFrame:
    return pd.DataFrame({
        "Professor": ["Maria da Silva", "João Pereira", "Fernanda Souza", "Ricardo Alves"],
    })


def criar_templates():
    """Cria os arquivos de exemplo em dados/ caso não existam."""
    config.DADOS_DIR.mkdir(parents=True, exist_ok=True)
    garantir_planilha(config.OCORRENCIAS_XLSX, config.COLUNAS_OCORRENCIAS)
    garantir_planilha(config.AVISOS_XLSX, config.COLUNAS_AVISOS)

    path = config.CADASTRO_XLSX
    falta_alunos = not _sheet_existe(path, config.SHEET_ALUNOS)
    falta_professores = not _sheet_existe(path, config.SHEET_PROFESSORES)
    if not (falta_alunos or falta_professores):
        return
    with _lock(path):
        if falta_alunos and not _sheet_existe(path, config.SHEET_ALUNOS):
            _escrever_sheet(path, _dados_alunos_exemplo(), config.SHEET_ALUNOS)
        if falta_professores and not _sheet_existe(path, config.SHEET_PROFESSORES):
            _escrever_sheet(path, _dados_professores_exemplo(), config.SHEET_PROFESSORES)


def carregar_series() -> list[str]:
    df = ler_planilha(config.CADASTRO_XLSX, config.COLUNAS_ALUNOS, config.SHEET_ALUNOS)
    if df.empty:
        return []
    return sorted({str(s).strip() for s in df["Serie"].dropna() if str(s).strip()})


def carregar_alunos(serie: str) -> list[str]:
    df = ler_planilha(config.CADASTRO_XLSX, config.COLUNAS_ALUNOS, config.SHEET_ALUNOS)
    if df.empty or not serie:
        return []
    mask = df["Serie"].astype(str).str.strip() == serie
    return sorted({str(a).strip() for a in df.loc[mask, "Aluno"].dropna() if str(a).strip()})


def carregar_professores() -> list[str]:
    df = ler_planilha(config.CADASTRO_XLSX, config.COLUNAS_PROFESSORES, config.SHEET_PROFESSORES)
    if df.empty:
        return []
    return sorted({str(p).strip() for p in df["Professor"].dropna() if str(p).strip()})
