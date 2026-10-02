import streamlit as st

from core import config, excel_io

st.set_page_config(page_title="Painel de Ocorrências", layout="centered")

excel_io.criar_templates()

st.title("Painel de Ocorrências")
st.write("Escolha o perfil para continuar:")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Professor")
    st.caption("Registrar ocorrências e avisos da turma.")
    if st.button("Entrar como Professor", type="primary", use_container_width=True):
        st.session_state["perfil"] = "Professor"
        st.switch_page("pages/1_Professor.py")

with col2:
    st.subheader("Gestor")
    st.caption("Receber e ler os alertas enviados pelos professores.")
    if st.button("Entrar como Gestor", use_container_width=True):
        st.session_state["perfil"] = "Gestor"
        st.switch_page("pages/2_Gestor.py")

_headers = {str(k).lower(): str(v) for k, v in st.context.headers.items()}
_host = _headers.get("host", "").lower()
_na_nuvem = _host.endswith(".streamlit.app") or _host.endswith(".streamlit.io")

if not _na_nuvem:
    st.divider()

    with st.expander("Como acessar de outro computador ou celular (mesmo Wi-Fi)"):
        st.markdown(
            f"""
1. Este computador precisa estar com o painel aberto (`iniciar.bat`).
2. Na rede local, acesse no navegador:

**{config.url_local()}**

3. Professora e gestor podem abrir o mesmo endereço ao mesmo tempo.
"""
        )
        st.caption("Para descobrir o IP da máquina: prompt de comando → ipconfig")
