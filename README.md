# Painel de Ocorrências

App escolar feito com [Streamlit](https://streamlit.io) para registrar e acompanhar ocorrências e avisos da turma. Possui dois perfis de acesso: **Professor** (registra ocorrências e avisos) e **Gestor** (protegido por senha, lê os alertas e gera relatórios em gráfico).

**Acesse o app:** https://painel-ocorrencias.streamlit.app/

## Funcionalidades

- Tela inicial com escolha de perfil e botão **"Voltar ao início"** (menu lateral oculto).
- **Professor**: registro de ocorrências e avisos por série, aluno e professor.
- **Gestor** (senha definida via secret):
  - Aba **Alertas**: lista unificada de ocorrências e avisos com filtros (registro, status, busca, categoria) e atualização automática.
  - Aba **Relatórios**: gráficos com filtros de tipo de registro e de relatório:
    1. Quantidade de registros **por sala**;
    2. Quantidade de registros **por dia da semana** (últimos 7 dias).

## Como rodar localmente

Requisitos: Python 3.12 ou superior.

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

No Windows também pode usar o atalho `iniciar.bat`.

- Senha local do gestor: `gestoratento`
- O painel abre em `http://localhost:8501`; na rede local, use o IP da máquina (exibido na tela inicial).

## Estrutura do projeto

```
.
├── app.py                  # tela inicial (escolha de perfil)
├── pages/
│   ├── 1_Professor.py      # registro de ocorrências e avisos
│   └── 2_Gestor.py         # painel do gestor (senha, alertas, relatórios)
├── core/
│   ├── config.py           # constantes, senha e endereço local
│   └── excel_io.py         # leitura/gravação das planilhas
├── dados/
│   └── cadastro.xlsx       # séries, alunos e professores (versionado)
├── .streamlit/config.toml  # tema e menu lateral oculto
├── iniciar.bat             # atalho para iniciar no Windows
├── LICENSE                 # licença de uso
└── requirements.txt
```

## Observações sobre o deploy (Streamlit Community Cloud)

- Os dados de `ocorrencias.xlsx` e `avisos.xlsx` são **efêmeros**: a cada atualização de código/redeploy na nuvem, as planilhas são recriadas vazias — somente o que está no GitHub é restaurado.
- `dados/cadastro.xlsx` (séries, alunos e professores) está versionado no repositório.
- A senha da nuvem é definida em **Secrets** no painel de deploy, no formato `SENHA_GESTOR = "sua-senha"`; sem secret, vale o fallback `gestoratento`.
- A página do professor não possui senha — qualquer pessoa com o link pode registrar ocorrências.

## Licença

Este projeto está licenciado sob a **Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)** — veja o arquivo [LICENSE](LICENSE).

Resumo: você pode copiar, adaptar e redistribuir o código, desde que:

1. **Não use o material para fins comerciais**;
2. **Cite o autor**, por exemplo:

> Fernando Navarro — *Painel de Ocorrências* (https://github.com/fernandonavarrost-cpu/painel-ocorrencias)

## Autoria

Desenvolvido por **Fernando Navarro**.
