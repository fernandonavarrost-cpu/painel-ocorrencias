import altair as alt
import pandas as pd
import streamlit as st

from core import config, excel_io

st.set_page_config(page_title="Gestor", layout="wide")

excel_io.criar_templates()

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def _filtrar(df: pd.DataFrame, registro: str, status: str, busca: str,
             categorias: list[str]) -> pd.DataFrame:
    d = df
    if registro != "Todos":
        d = d[d["Registro"] == registro]
    if status != "Todos":
        d = d[d["Status"] == status]
    if categorias and registro != "Ocorrência":
        d = d[d["Registro"] == "Aviso"]
        d = d[d["Detalhe"].astype(str).apply(
            lambda t: any(c in str(t) for c in categorias)
        )]
    if busca.strip():
        termo = busca.strip().lower()
        colunas_txt = ["Aluno", "Professor", "Serie", "Registro", "Detalhe"]
        mascara = False
        for c in colunas_txt:
            mascara = mascara | d[c].astype(str).str.lower().str.contains(termo, na=False)
        d = d[mascara]
    return d


@st.fragment(run_every=config.AUTO_REFRESH_SEGUNDOS)
def painel_alertas():
    df = excel_io.carregar_alertas()

    if df.empty:
        st.info("Nenhuma ocorrência ou aviso registrado até o momento.")
        return

    total = len(df)
    pendentes = int((df["Status"] == config.STATUS_PENDENTE).sum())
    m1, m2, m3 = st.columns(3)
    m1.metric("Total de alertas", total)
    m2.metric("Pendentes", pendentes)
    m3.metric("Lidos", total - pendentes)

    f1, f2, f3, f4 = st.columns([2, 2, 3, 3])
    with f1:
        registro = st.selectbox(
            "Registro", ["Todos", "Ocorrência", "Aviso"], key="g_registro",
        )
    with f2:
        status = st.selectbox(
            "Status", ["Todos", config.STATUS_PENDENTE, config.STATUS_LIDO],
            key="g_status",
        )
    with f3:
        busca = st.text_input(
            "Buscar", key="g_busca",
            placeholder="Aluno, professor, série...",
        )
    with f4:
        categorias = st.multiselect(
            "Categoria do aviso", config.TIPOS_AVISO, key="g_categorias",
            disabled=registro == "Ocorrência",
        )

    filtrados = _filtrar(df, registro, status, busca, categorias)

    lista_col, detalhe_col = st.columns([5, 6])

    with lista_col:
        st.subheader(f"Alertas ({len(filtrados)})")
        if filtrados.empty:
            st.info("Nenhum alerta com esses filtros.")
        else:
            visiveis = filtrados.head(config.MAX_ALERTAS_LISTA)
            for _, linha in visiveis.iterrows():
                arquivo = str(linha["Arquivo"])
                id_reg = int(pd.to_numeric(linha["ID"]))
                rotulo = (
                    f"[{linha['Status']}] {linha['Registro']} nº {id_reg} · "
                    f"{linha['Aluno']} ({linha['Serie']}) · "
                    f"{excel_io.formatar_data(linha['Data'])}"
                )
                if st.button(rotulo, key=f"sel_{arquivo}_{id_reg}",
                             use_container_width=True):
                    st.session_state["detalhe"] = (arquivo, id_reg)
            if len(filtrados) > config.MAX_ALERTAS_LISTA:
                st.caption(
                    f"Mostrando {config.MAX_ALERTAS_LISTA} de {len(filtrados)}. "
                    "Use os filtros para ver os demais."
                )

    with detalhe_col:
        st.subheader("Detalhes")
        sel = st.session_state.get("detalhe")
        if not sel:
            st.info("Selecione um alerta na lista ao lado para ler as informações.")
            return

        id_sel = pd.to_numeric(df["ID"], errors="coerce")
        alvo = df[(df["Arquivo"] == sel[0]) & (id_sel == sel[1])]
        if alvo.empty:
            st.warning("Este registro não existe mais.")
            return

        linha = alvo.iloc[0]
        st.markdown(f"### {linha['Registro']} nº {int(pd.to_numeric(linha['ID']))}")
        c1, c2 = st.columns(2)
        c1.markdown(f"**Data:** {excel_io.formatar_data(linha['Data'])}")
        c2.markdown(f"**Série:** {linha['Serie']}")
        c1, c2 = st.columns(2)
        c1.markdown(f"**Aluno:** {linha['Aluno']}")
        c2.markdown(f"**Professor:** {linha['Professor']}")
        st.markdown(f"**Status:** {linha['Status']}")
        st.markdown("**Informação:**")
        st.write(str(linha["Detalhe"]))
        st.caption(f"Enviado em {linha['Criado_em']}")

        if linha["Status"] == config.STATUS_PENDENTE:
            if st.button("Marcar como lido", type="primary", key="btn_lido"):
                try:
                    excel_io.atualizar_alerta(
                        str(linha["Arquivo"]), int(pd.to_numeric(linha["ID"])),
                        config.STATUS_LIDO,
                    )
                except PermissionError:
                    st.error(
                        "Não foi possível salvar: o arquivo do Excel está aberto. "
                        "Feche-o e tente de novo."
                    )
                else:
                    st.session_state["msg_gestor"] = "Alerta marcado como lido."
                    st.rerun()
        else:
            st.caption("Este alerta já foi lido.")

    msg = st.session_state.pop("msg_gestor", None)
    if msg:
        st.success(msg)


def _relatorio_por_sala(dados: pd.DataFrame):
    d = dados.dropna(subset=["Serie"])
    d = d[d["Serie"].astype(str).str.strip() != ""]
    if d.empty:
        st.info("Nenhum registro com esses filtros.")
        return

    contagem = d.groupby("Serie").size().reset_index(name="Quantidade")
    contagem = contagem.sort_values(["Quantidade", "Serie"], ascending=[False, True])

    grafico = (
        alt.Chart(contagem)
        .mark_bar(color="#ff4b4b")
        .encode(
            x=alt.X(
                "Serie:N",
                title="Sala",
                sort=alt.EncodingSortField(field="Quantidade", order="descending"),
            ),
            y=alt.Y("Quantidade:Q", title="Quantidade", scale=alt.Scale(zero=True)),
            tooltip=["Serie", "Quantidade"],
        )
        .properties(height=400)
    )
    st.altair_chart(grafico)
    st.caption(
        f"Total: {int(contagem['Quantidade'].sum())} registro(s) "
        f"em {len(contagem)} sala(s)."
    )


def _relatorio_por_dia_semana(dados: pd.DataFrame):
    d = dados.dropna(subset=["Data"])
    if d.empty:
        st.info("Nenhum registro com esses filtros.")
        return

    hoje = pd.Timestamp.today().normalize()
    inicio = hoje - pd.Timedelta(days=6)
    datas = d["Data"].dt.normalize()
    janela = datas[(datas >= inicio) & (datas <= hoje)]

    contagem = janela.dt.dayofweek.value_counts().reindex(range(7), fill_value=0)
    if int(contagem.sum()) == 0:
        st.info(f"Nenhum registro entre {inicio:%d/%m/%Y} e {hoje:%d/%m/%Y}.")
        return

    df_graf = pd.DataFrame({
        "Dia da semana": DIAS_SEMANA,
        "Quantidade": contagem.to_numpy(),
    })

    grafico = (
        alt.Chart(df_graf)
        .mark_bar(color="#ff4b4b")
        .encode(
            x=alt.X("Dia da semana:N", title="Dia da semana", sort=DIAS_SEMANA),
            y=alt.Y("Quantidade:Q", title="Quantidade", scale=alt.Scale(zero=True)),
            tooltip=["Dia da semana", "Quantidade"],
        )
        .properties(height=400)
    )
    st.altair_chart(grafico)

    total = int(contagem.sum())
    pico = DIAS_SEMANA[int(contagem.to_numpy().argmax())]
    st.caption(
        f"Total de {inicio:%d/%m} a {hoje:%d/%m}: {total} registro(s). "
        f"Dia com mais registros: {pico}."
    )


def relatorios():
    df = excel_io.carregar_alertas()

    if df.empty:
        st.info("Nenhuma ocorrência ou aviso registrado até o momento.")
        return

    f1, f2 = st.columns([1, 2])
    with f1:
        registro = st.selectbox(
            "Tipo de registro", ["Todos", "Ocorrência", "Aviso"], key="rel_registro",
        )
    with f2:
        relatorio = st.selectbox(
            "Relatório",
            ["Quantidade por sala", "Quantidade por dia da semana (últimos 7 dias)"],
            key="rel_tipo",
        )

    dados = df if registro == "Todos" else df[df["Registro"] == registro]
    dados = dados.copy()
    dados["Data"] = pd.to_datetime(dados["Data"], errors="coerce")

    if dados.empty:
        st.info("Nenhum registro com esses filtros.")
        return

    if relatorio == "Quantidade por sala":
        _relatorio_por_sala(dados)
    else:
        _relatorio_por_dia_semana(dados)


if st.sidebar.button("← Voltar ao início", use_container_width=True,
                     key="btn_voltar_inicio_gestor"):
    st.session_state.pop("detalhe", None)
    st.session_state.pop("perfil", None)
    st.switch_page("app.py")

# ----- acesso ao painel do gestor (senha vale pela sessão) -----
if not st.session_state.get("gestor_autenticado"):
    st.title("Painel do Gestor")
    st.write("Informe a senha para acessar o painel:")
    senha = st.text_input("Senha", type="password", key="gestor_senha")
    if st.button("Entrar", type="primary", key="btn_entrar_gestor"):
        if senha == config.SENHA_GESTOR:
            st.session_state["gestor_autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

st.title("Painel do Gestor")

tab_alertas, tab_relatorios = st.tabs(["Alertas", "Relatórios"])

with tab_alertas:
    st.caption(
        f"Alertas recebidos dos professores · atualização automática a cada "
        f"{config.AUTO_REFRESH_SEGUNDOS} segundos"
    )
    painel_alertas()

with tab_relatorios:
    st.caption(
        "Ocorrências e avisos em gráfico · filtros de tipo de registro e de relatório"
    )
    relatorios()
