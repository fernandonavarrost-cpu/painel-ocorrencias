from datetime import date, datetime

import streamlit as st

from core import config, excel_io

st.set_page_config(page_title="Professor", layout="wide")

excel_io.criar_templates()

if st.sidebar.button("← Voltar ao início", use_container_width=True,
                     key="btn_voltar_inicio_prof"):
    st.session_state.pop("perfil", None)
    st.switch_page("app.py")

# ----- limpeza dos formulários após envio (antes de criar os widgets) -----
if st.session_state.pop("reset_ocorrencia", False):
    st.session_state["occ_serie"] = None
    st.session_state["occ_aluno"] = None
    st.session_state["occ_professor"] = None
    st.session_state["occ_data"] = date.today()
    st.session_state["occ_descricao"] = ""

if st.session_state.pop("reset_aviso", False):
    st.session_state["av_serie"] = None
    st.session_state["av_aluno"] = None
    st.session_state["av_professor"] = None
    st.session_state["av_data"] = date.today()
    for i in range(len(config.TIPOS_AVISO)):
        st.session_state[f"av_tipo_{i}"] = False

# ----- se a série mudou, o aluno selecionado deixa de ser válido -----
if st.session_state.get("occ_serie") != st.session_state.get("_serie_occ_ant"):
    st.session_state["occ_aluno"] = None
    st.session_state["_serie_occ_ant"] = st.session_state.get("occ_serie")

if st.session_state.get("av_serie") != st.session_state.get("_serie_av_ant"):
    st.session_state["av_aluno"] = None
    st.session_state["_serie_av_ant"] = st.session_state.get("av_serie")

st.title("Página do Professor")
st.caption(f"Perfil: {st.session_state.get('perfil', 'Professor')}")

series = excel_io.carregar_series()
professores = excel_io.carregar_professores()

if not series or not professores:
    st.warning(
        "Não encontrei séries/alunos ou professores em "
        "`dados/cadastro.xlsx`. Verifique as abas Alunos e Professores."
    )

tab_ocorrencia, tab_aviso = st.tabs(["Ocorrência", "Aviso"])

with tab_ocorrencia:
    msg = st.session_state.get("msg_ocorrencia")
    if msg:
        st.success(msg)

    col1, col2, col3 = st.columns(3)
    with col1:
        serie = st.selectbox(
            "Série do aluno", series, key="occ_serie",
            index=None, placeholder="Selecione a série",
            disabled=not series,
        )
    with col2:
        alunos = excel_io.carregar_alunos(serie) if serie else []
        aluno = st.selectbox(
            "Nome do aluno", alunos, key="occ_aluno",
            index=None, placeholder="Selecione o aluno",
            disabled=not serie or not alunos,
        )
    with col3:
        data = st.date_input("Data", key="occ_data")

    professor = st.selectbox(
        "Professor", professores, key="occ_professor",
        index=None, placeholder="Selecione o professor",
        disabled=not professores,
    )
    descricao = st.text_area(
        "Descrição da ocorrência", key="occ_descricao", height=180,
        placeholder="Descreva o que aconteceu...",
    )

    if st.button("Enviar ocorrência", type="primary", key="btn_enviar_ocorrencia"):
        erros = []
        if not serie:
            erros.append("selecione a série")
        if not aluno:
            erros.append("selecione o aluno")
        if not professor:
            erros.append("selecione o professor")
        if not str(descricao).strip():
            erros.append("escreva a descrição da ocorrência")
        if erros:
            st.error("Antes de enviar: " + ", ".join(erros) + ".")
        else:
            try:
                novo_id = excel_io.adicionar_linha(
                    config.OCORRENCIAS_XLSX,
                    {
                        "Data": data,
                        "Serie": serie,
                        "Aluno": aluno,
                        "Professor": professor,
                        "Descricao": str(descricao).strip(),
                        "Status": config.STATUS_PENDENTE,
                        "Criado_em": f"{date.today():%d/%m/%Y} {datetime.now():%H:%M}",
                    },
                    config.COLUNAS_OCORRENCIAS,
                )
            except PermissionError:
                st.error("Não foi possível salvar: o arquivo "
                         "`dados/ocorrencias.xlsx` está aberto no Excel. Feche e tente de novo.")
            else:
                st.session_state["msg_ocorrencia"] = (
                    f"Ocorrência nº {novo_id} enviada com sucesso."
                )
                st.session_state["reset_ocorrencia"] = True
                st.rerun()

with tab_aviso:
    msg = st.session_state.get("msg_aviso")
    if msg:
        st.success(msg)

    col1, col2, col3 = st.columns(3)
    with col1:
        serie_a = st.selectbox(
            "Série do aluno", series, key="av_serie",
            index=None, placeholder="Selecione a série",
            disabled=not series,
        )
    with col2:
        alunos_a = excel_io.carregar_alunos(serie_a) if serie_a else []
        aluno_a = st.selectbox(
            "Nome do aluno", alunos_a, key="av_aluno",
            index=None, placeholder="Selecione o aluno",
            disabled=not serie_a or not alunos_a,
        )
    with col3:
        data_a = st.date_input("Data", key="av_data")

    professor_a = st.selectbox(
        "Professor", professores, key="av_professor",
        index=None, placeholder="Selecione o professor",
        disabled=not professores,
    )

    st.write("Selecione o tipo do aviso:")
    cols_tipos = st.columns(2)
    tipos_marcados = []
    for i, tipo in enumerate(config.TIPOS_AVISO):
        with cols_tipos[i % 2]:
            marcado = st.checkbox(tipo, key=f"av_tipo_{i}")
            if marcado:
                tipos_marcados.append(tipo)

    if st.button("Enviar aviso", type="primary", key="btn_enviar_aviso"):
        erros = []
        if not serie_a:
            erros.append("selecione a série")
        if not aluno_a:
            erros.append("selecione o aluno")
        if not professor_a:
            erros.append("selecione o professor")
        if not tipos_marcados:
            erros.append("marque pelo menos um tipo de aviso")
        if erros:
            st.error("Antes de enviar: " + ", ".join(erros) + ".")
        else:
            try:
                novo_id = excel_io.adicionar_linha(
                    config.AVISOS_XLSX,
                    {
                        "Data": data_a,
                        "Serie": serie_a,
                        "Aluno": aluno_a,
                        "Professor": professor_a,
                        "Tipos": "; ".join(tipos_marcados),
                        "Status": config.STATUS_PENDENTE,
                        "Criado_em": f"{date.today():%d/%m/%Y} {datetime.now():%H:%M}",
                    },
                    config.COLUNAS_AVISOS,
                )
            except PermissionError:
                st.error("Não foi possível salvar: o arquivo "
                         "`dados/avisos.xlsx` está aberto no Excel. Feche e tente de novo.")
            else:
                st.session_state["msg_aviso"] = f"Aviso nº {novo_id} enviado com sucesso."
                st.session_state["reset_aviso"] = True
                st.rerun()
