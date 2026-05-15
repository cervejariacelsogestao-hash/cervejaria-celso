# 🍺 Cervejaria do Celso — Gestão Interna

Ferramenta de gestão interna para a Cervejaria do Celso, Campo de Ourique, Lisboa.

**Stack**: Google Sheets (dados) + Streamlit (interface) + Google Apps Script (automações)

**Custo mensal**: €0

---

## Setup inicial (15 minutos)

### 1. Pré-requisitos

- Python 3.11+
- Conta Google com acesso ao projecto `cervejaria-celso` no Google Cloud
- Ficheiro JSON da service account `celso-gestao`
- Repositório GitHub clonado localmente

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Abre `.streamlit/secrets.toml` e preenche com:
- Os valores do ficheiro JSON da service account (abre o JSON e copia campo a campo)
- O email admin: `cervejariacelsogestao@gmail.com`

### 4. Correr localmente

```bash
streamlit run app.py
```

Abre `http://localhost:8501` no browser.

### 5. Inicializar a base de dados

1. Faz login com `cervejariacelsogestao@gmail.com` / `celso2024`
2. Na sidebar clica **"⚙️ Setup Base de Dados"**
3. Clica **"Inicializar Base de Dados"**
4. Vai criar o Google Sheet `Cervejaria_Celso_DB` com todas as 16 worksheets
5. **Partilha o Sheet** com a service account: `celso-gestao@cervejaria-celso.iam.gserviceaccount.com` (role: Editor)

### 6. Deploy no Streamlit Cloud (gratuito)

1. Vai a [share.streamlit.io](https://share.streamlit.io)
2. Liga a tua conta GitHub
3. Selecciona o repo `cervejaria-celso`, branch `main`, ficheiro `app.py`
4. Em **"Advanced settings"** → **"Secrets"**, cola o conteúdo do teu `secrets.toml`
5. Clica **Deploy**
6. URL fica tipo: `cervejaria-celso.streamlit.app`

---

## Utilizadores e passwords

| Email | Role | Password inicial |
|-------|------|-----------------|
| cervejariacelsogestao@gmail.com | admin | celso2024 |

**Altera a password após o primeiro login** — edita directamente na sheet `users`.

## Roles e permissões

| Módulo | admin | dono | gerente |
|--------|-------|------|---------|
| Dashboard | ✅ | ✅ | ✅ |
| Caixa Diária | ✅ | ✅ | ✅ |
| Fichas Técnicas | ✅ | ✅ | ❌ |
| Food Cost | ✅ | ✅ | ❌ |
| Stocks | ✅ | ✅ | ❌ |
| Fornecedores | ✅ | ✅ | ❌ |
| Menu Engineering | ✅ | ✅ | ❌ |
| Pessoal | ✅ | ✅ | ❌ |
| P&L Mensal | ✅ | ✅ | ❌ |
| Importar Winrest | ✅ | ❌ | ❌ |

---

## Estrutura do projecto

```
cervejaria-celso/
├── app.py                    # Entry point
├── auth.py                   # Autenticação e roles
├── requirements.txt
├── .streamlit/
│   ├── config.toml           # Tema (laranja/preto)
│   └── secrets.toml.example  # Template de secrets
├── data/
│   ├── sheets_client.py      # Wrapper gspread + CRUD
│   ├── schema.py             # Definição e criação das 16 sheets
│   └── seed.py               # Dados de teste (Sprint 7)
├── modules/                  # Um ficheiro por módulo (Sprints 2-6)
├── utils/                    # Formatadores e cálculos comuns
├── apps_script/              # Automações Google Sheets
└── docs/                     # Manuais
```

---

## Sprints

| Sprint | Semana | Conteúdo |
|--------|--------|----------|
| 1 | 1 | ✅ Fundações (este README) |
| 2 | 2 | Caixa diária + Dashboard |
| 3 | 3 | Fichas técnicas + Food cost |
| 4 | 4 | Importação Winrest + Menu engineering |
| 5 | 5 | Stocks + Fornecedores |
| 6 | 6 | Pessoal + P&L |
| 7 | 7 | Polimento + Manuais |

---

## Segurança

- `.streamlit/secrets.toml` está no `.gitignore` — **nunca fazer commit**
- A service account só tem acesso ao spreadsheet específico
- Passwords guardadas como hash sha256 na sheet `users`
- Dados alojados em Google Sheets (infraestrutura Google, RGPD aceitável com conta empresarial)
