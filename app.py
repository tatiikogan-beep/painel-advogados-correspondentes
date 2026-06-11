import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
from supabase import create_client, Client
import io
import base64
import os

st.set_page_config(
    page_title="Painel - Advogados Correspondentes",
    page_icon="\u2696\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded"
)

COR_VERMELHO  = "#8B1A1A"
COR_DOURADO   = "#C8A951"
COR_DESTAQUE  = "#A52A2A"
COR_BRANCO    = "#FFFFFF"
COR_CINZA_BG  = "#F5F5F5"

def get_logo_b64():
    path = "logo.png"
    if os.path.isfile(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

st.markdown(f"""
<style>
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COR_VERMELHO} 0%, #5C1010 100%);
    }}
    [data-testid="stSidebar"] * {{
        color: {COR_BRANCO} !important;
    }}
    .stButton > button {{
        background-color: {COR_VERMELHO};
        color: {COR_BRANCO};
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }}
    .stButton > button:hover {{
        background-color: {COR_DESTAQUE};
        color: {COR_BRANCO};
    }}
    .metric-card {{
        background: {COR_BRANCO};
        border-left: 5px solid {COR_DOURADO};
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    .metric-card h3 {{ margin: 0; font-size: 2rem; color: {COR_VERMELHO}; }}
    .metric-card p  {{ margin: 0; font-size: 0.85rem; color: #555; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["URL_SUPABASE"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=60)
def load_data():
    try:
        sb = get_supabase()
        resp = sb.table("advogados").select("*").execute()
        return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_audiencias():
    """Carrega audiências salvas no Supabase com paginação (evita limite de 1000)."""
    try:
        sb = get_supabase()
        todos = []
        passo = 1000
        inicio = 0
        while True:
            resp = sb.table("audiencias").select("*").range(inicio, inicio + passo - 1).execute()
            lote = resp.data or []
            todos.extend(lote)
            if len(lote) < passo:
                break
            inicio += passo
        return pd.DataFrame(todos) if todos else pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar audiências: {e}")
        return pd.DataFrame()

def _normaliza_txt(s):
    """minúsculas, sem acentos, espaços colapsados."""
    import unicodedata, re
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s

# Agrupamentos conhecidos: assinatura normalizada -> rótulo canônico exibido
GRUPOS_CLIENTE = {
    "imc saste": "IMC Saste Construções, Serviços e Comércio Ltda.",
    "gpm": "GPM - Pague Menos",
    "pague menos": "GPM - Pague Menos",
}

def cliente_canonico(nome):
    """Reduz variações de grafia a um rótulo canônico (correspondência parcial)."""
    n = _normaliza_txt(nome)
    if not n:
        return ""
    for chave, rotulo in GRUPOS_CLIENTE.items():
        if chave in n:
            return rotulo
    # título capitalizado como fallback de agrupamento por nome normalizado
    return " ".join(w.capitalize() for w in n.split())

def insert_data(record: dict):
    try:
        sb = get_supabase()
        sb.table("advogados").insert(record).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir: {e}")
        return False

def update_data(record_id: int, fields: dict):
    try:
        sb = get_supabase()
        sb.table("advogados").update(fields).eq("id", record_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False

def delete_data(record_id: int):
    try:
        sb = get_supabase()
        sb.table("advogados").delete().eq("id", record_id).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False

ESTADOS = ["", "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
           "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
TIPOS   = ["", "Audiencia", "Diligencia", "Pericia", "Protocolo", "Outro"]

ETIQUETAS = ["", "Com contrato", "Aguardando retorno", "Fora do perfil", "Sem interesse", "Contato bloqueado"]
ETIQUETAS_CORES = {
    "Com contrato":      "#28a745",
    "Aguardando retorno":"#007bff",
    "Fora do perfil":    "#ffc107",
    "Sem interesse":     "#fd7e14",
    "Contato bloqueado": "#dc3545",
    "":                  "#cccccc",
}

logo_b64 = get_logo_b64()
if logo_b64:
    st.sidebar.markdown(
        f'<div style="text-align:center;padding:10px 0 20px;">'
        f'<img src="data:image/png;base64,{logo_b64}" style="width:140px;border-radius:8px;"></div>',
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(
        f'<div style="text-align:center;padding:10px 0;color:{COR_DOURADO};'
        f'font-size:1.2rem;font-weight:700;">IG Advogados</div>',
        unsafe_allow_html=True
    )

st.sidebar.markdown(f'<p style="color:{COR_DOURADO};font-size:0.75rem;text-align:center;'
                    f'margin-bottom:16px;">Advogados Correspondentes</p>', unsafe_allow_html=True)

PAGINAS = ["Dashboard", "Cadastro", "Importar Planilha", "Registros", "Editar/Excluir", "Gestão Financeira"]
st.sidebar.markdown('<p style="font-size:0.7rem;color:rgba(255,255,255,0.5);'
                    'margin-bottom:4px;">NAVEGACAO</p>', unsafe_allow_html=True)
pagina = st.sidebar.radio("NAVEGACAO", PAGINAS, label_visibility="collapsed")

if logo_b64:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:16px;'
        f'background:linear-gradient(90deg,{COR_VERMELHO},{COR_DESTAQUE});'
        f'padding:14px 24px;border-radius:10px;margin-bottom:24px;">'
        f'<img src="data:image/png;base64,{logo_b64}" style="height:56px;border-radius:6px;">'
        f'<div><h2 style="margin:0;color:{COR_BRANCO};">Advogados Correspondentes</h2>'
        f'<p style="margin:0;color:{COR_DOURADO};font-size:0.85rem;">'
        f'Imaculada Gordiano Sociedade de Advogados</p></div></div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f'<div style="background:linear-gradient(90deg,{COR_VERMELHO},{COR_DESTAQUE});'
        f'padding:14px 24px;border-radius:10px;margin-bottom:24px;">'
        f'<h2 style="margin:0;color:{COR_BRANCO};">Advogados Correspondentes</h2>'
        f'<p style="margin:0;color:{COR_DOURADO};font-size:0.85rem;">'
        f'Imaculada Gordiano Sociedade de Advogados</p></div>',
        unsafe_allow_html=True
    )

# ── DASHBOARD ──────────────────────────────────────────────────────────────
if pagina == "Dashboard":
    df = load_data()
    total = len(df)
    municipios = df["cidade"].nunique() if "cidade" in df.columns and not df.empty else 0
    ufs = df["estado"].nunique() if "estado" in df.columns and not df.empty else 0
    empresas = df["empresa"].nunique() if "empresa" in df.columns and not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, total,     "Total Correspondentes"),
        (c2, municipios,"Municipios Atendidos"),
        (c3, ufs,       "UFs Atendidas"),
        (c4, empresas,  "Empresas"),
    ]:
        col.markdown(
            f'<div class="metric-card"><h3>{val}</h3><p>{label}</p></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        if "estado" in df.columns:
            cnt_uf = df["estado"].value_counts().reset_index()
            cnt_uf.columns = ["Estado", "Quantidade"]
            fig1 = px.bar(cnt_uf, x="Estado", y="Quantidade",
                          title="Correspondentes por Estado",
                          color_discrete_sequence=[COR_VERMELHO])
            col_g1.plotly_chart(fig1, use_container_width=True)
        if "tipo" in df.columns:
            cnt_tipo = df["tipo"].value_counts().reset_index()
            cnt_tipo.columns = ["Tipo", "Quantidade"]
            fig2 = px.pie(cnt_tipo, names="Tipo", values="Quantidade",
                          title="Distribuicao por Tipo",
                          color_discrete_sequence=[COR_VERMELHO, COR_DOURADO,
                                                   COR_DESTAQUE, "#D2691E", "#8B4513"])
            col_g2.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Nenhum dado cadastrado ainda.")


    # ── Regra de pagamento por cliente (IMC Saste) ──
    st.markdown("---")
    st.markdown("#### Regras de pagamento por cliente")
    df_aud = load_audiencias()
    hoje_d = date.today()
    ini_mes = hoje_d.replace(day=1)
    meses_pt = ["janeiro","fevereiro","março","abril","maio","junho","julho",
                "agosto","setembro","outubro","novembro","dezembro"]
    st.caption(f"Referência: {meses_pt[hoje_d.month-1]}/{hoje_d.year} (mês vigente).")
    qtd_imc = 0
    if not df_aud.empty and "data" in df_aud.columns and "cliente" in df_aud.columns:
        _dt = pd.to_datetime(df_aud["data"], errors="coerce", dayfirst=True)
        _mes = df_aud[(_dt >= pd.Timestamp(ini_mes)) & (_dt < pd.Timestamp(hoje_d) + pd.Timedelta(days=1))]
        _canon = _mes["cliente"].apply(cliente_canonico)
        qtd_imc = int((_canon == "IMC Saste Construções, Serviços e Comércio Ltda.").sum())
    meta_imc = 30
    atingida = qtd_imc > meta_imc
    pct = min(100, int(round((qtd_imc / meta_imc) * 100))) if meta_imc else 0
    cor_borda = COR_DOURADO if atingida else COR_VERMELHO
    cor_barra = "#2E9E5B" if atingida else COR_VERMELHO
    selo = ('<span style="background:#2E9E5B;color:#fff;padding:3px 12px;border-radius:12px;font-size:0.72rem;font-weight:700;">Regra atingida</span>'
            if atingida else
            '<span style="background:#eee;color:#777;padding:3px 12px;border-radius:12px;font-size:0.72rem;font-weight:600;">Em andamento</span>')
    ponto = f'<span style="width:12px;height:12px;border-radius:50%;background:{"#2E9E5B" if atingida else "#ccc"};display:inline-block;"></span>'
    st.markdown(
        f'<div style="background:#fff;border-left:5px solid {cor_borda};border-radius:8px;padding:16px 18px;box-shadow:0 2px 8px rgba(0,0,0,0.08);max-width:520px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;"><strong style="color:{COR_VERMELHO};">IMC Saste Construções, Serviços e Comércio Ltda.</strong>{ponto}</div>'
        f'<p style="margin:6px 0 2px;color:#555;font-size:0.82rem;">Quantidade superior a 30 audiências realizadas</p>'
        f'<div style="font-size:1.6rem;font-weight:700;color:{COR_VERMELHO};">{qtd_imc} <span style="font-size:0.85rem;color:#888;font-weight:400;">/ meta {meta_imc} audiências</span></div>'
        f'<div style="background:#eee;border-radius:6px;height:8px;margin:8px 0;"><div style="width:{pct}%;background:{cor_barra};height:8px;border-radius:6px;"></div></div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;"><span style="color:#777;font-size:0.78rem;">{pct}% da meta</span>{selo}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
# ── CADASTRO ───────────────────────────────────────────────────────────────
elif pagina == "Cadastro":
    st.subheader("Cadastrar Correspondente")
    with st.form("form_cadastro"):
        c1, c2 = st.columns(2)
        nome      = c1.text_input("Nome *")
        oab       = c2.text_input("OAB")
        telefone  = c1.text_input("Telefone")
        cidade    = c2.text_input("Cidade")
        estado    = c1.selectbox("Estado", ESTADOS)
        empresa   = c2.text_input("Empresa")
        cliente   = c1.text_input("Cliente")
        tipo      = c2.selectbox("Tipo de Servico", TIPOS)
        data_srv  = c1.date_input("Data do Servico", value=date.today())
        pagamento = c2.text_input("Pagamento (R$)")
        obs       = st.text_area("Observacoes", height=80)
        etiqueta = st.selectbox("Etiqueta", ETIQUETAS)
        if etiqueta:
            cor = ETIQUETAS_CORES.get(etiqueta, "#cccccc")
            st.markdown(f'<div style="display:inline-block;background:{cor};color:white;padding:4px 14px;border-radius:12px;font-weight:600;">{etiqueta}</div>', unsafe_allow_html=True)
        enviado   = st.form_submit_button("Salvar", use_container_width=True)

    if enviado:
        if not nome:
            st.error("O campo Nome e obrigatorio.")
        else:
            rec = {
                "nome":      nome,
                "oab":       oab       or None,
                "telefone":  telefone  or None,
                "cidade":    cidade    or None,
                "estado":    estado    or None,
                "empresa":   empresa   or None,
                "cliente":   cliente   or None,
                "tipo":      tipo      or None,
                "data":      str(data_srv),
                "pagamento": pagamento or None,
                "obs":       obs       or None,
                "etiqueta": etiqueta  or None,
            }
            if insert_data(rec):
                st.success("Correspondente cadastrado!")

# ── IMPORTAR PLANILHA ──────────────────────────────────────────────────────
elif pagina == "Importar Planilha":
    st.subheader("Importacao em Lote")

    st.info("""
    **Formato esperado da planilha (CSV ou Excel):**

    | nome | oab | telefone | cidade | estado | empresa | cliente | tipo | data | pagamento | obs |
    |------|-----|----------|--------|--------|---------|---------|------|------|-----------|-----|

    - A coluna **nome** e obrigatoria.
    - Datas no formato **YYYY-MM-DD** (ex.: 2024-05-20).
    - Os demais campos sao opcionais.
    """)

    modelo_csv = "nome,oab,telefone,cidade,estado,empresa,cliente,tipo,data,pagamento,obs\n"
    modelo_csv += "Joao Silva,OAB/SP 12345,(11)99999-0000,Sao Paulo,SP,Empresa A,Cliente X,Audiencia,2024-05-20,500.00,Observacao\n"
    st.download_button(
        label="Baixar modelo CSV",
        data=modelo_csv,
        file_name="modelo_correspondentes.csv",
        mime="text/csv"
    )

    arquivo = st.file_uploader("Enviar planilha", type=["csv", "xlsx", "xls"])
    if arquivo:
        try:
            if arquivo.name.endswith(".csv"):
                df_imp = pd.read_csv(arquivo)
            else:
                df_imp = pd.read_excel(arquivo)

            st.write("Previa dos dados:")
            st.dataframe(df_imp.head(10), hide_index=True)

            COLS = ["nome","oab","telefone","cidade","estado","empresa",
                    "cliente","tipo","data","pagamento","obs","etiqueta"]
            missing = [c for c in ["nome"] if c not in df_imp.columns]
            if missing:
                st.error(f"Coluna obrigatoria ausente: {missing}")
            else:
                for col in COLS:
                    if col not in df_imp.columns:
                        df_imp[col] = None

                if st.button("Importar todos os registros", type="primary"):
                    erros = 0
                    for _, row in df_imp.iterrows():
                        rec = {c: (str(row[c]) if pd.notna(row.get(c)) else None) for c in COLS}
                        if not rec.get("nome"):
                            erros += 1
                            continue
                        if not insert_data(rec):
                            erros += 1
                    if erros:
                        st.warning(f"Importacao concluida com {erros} erro(s).")
                    else:
                        st.success("Todos os registros importados!")
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

# ── REGISTROS ──────────────────────────────────────────────────────────────
elif pagina == "Registros":
    st.subheader("Registros Cadastrados")
    df = load_data()
    if df.empty:
        st.info("Nenhum registro encontrado.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        filtro_nome     = col1.text_input("Buscar por Nome")
        filtro_estado   = col2.selectbox("Filtrar por Estado", [""] + ESTADOS[1:])
        filtro_cidade   = col3.text_input("Filtrar por Cidade")
        filtro_etiqueta = col4.selectbox("Filtrar por Etiqueta", [""] + [e for e in ETIQUETAS if e])

        dff = df.copy()
        for col in dff.columns:
            if dff[col].dtype == object:
                dff[col] = dff[col].fillna("")

        if filtro_nome:
            dff = dff[dff["nome"].str.contains(filtro_nome, case=False, na=False)]
        if filtro_estado:
            dff = dff[dff["estado"] == filtro_estado]
        if filtro_cidade:
            dff = dff[dff["cidade"].str.contains(filtro_cidade, case=False, na=False)]
        if filtro_etiqueta:
            dff = dff[dff["etiqueta"] == filtro_etiqueta]

        st.write(f"**{len(dff)} registro(s) encontrado(s)**")

        # Exibir tabela com bolinha colorida da etiqueta
        display_cols = [c for c in ["id","nome","oab","telefone","cidade","estado","empresa","cliente","tipo"] if c in dff.columns]
        header_html = "".join(f"<th>{c}</th>" for c in display_cols) + "<th>etiqueta</th>"
        rows_html = ""
        for _, row in dff.iterrows():
            cells = "".join(f"<td>{row.get(c,'')}</td>" for c in display_cols)
            etiq = str(row.get("etiqueta","") or "").strip()
            etiq = "" if etiq.lower() in ("nan", "none", "null") else etiq
            cor  = ETIQUETAS_CORES.get(etiq, "#cccccc")
            if etiq:
                etiq_html = f'<span style="display:inline-flex;align-items:center;gap:6px;"><span style="width:12px;height:12px;border-radius:50%;background:{cor};display:inline-block;flex-shrink:0;"></span>{etiq}</span>'
            else:
                etiq_html = ""
            rows_html += f"<tr>{cells}<td>{etiq_html}</td></tr>"
        table_html = (
            '<style>.etiq-table{width:100%;border-collapse:collapse;font-size:13px}'
            '.etiq-table th,.etiq-table td{padding:6px 10px;border:1px solid #e0e0e0;text-align:left}'
            '.etiq-table th{background:#f5f5f5;font-weight:600}'
            '.etiq-table tr:hover{background:#fafafa}</style>'
            f'<div style="overflow-x:auto;"><table class="etiq-table">'
            f'<thead><tr>{header_html}</tr></thead>'
            f'<tbody>{rows_html}</tbody></table></div>'
        )
        st.markdown(table_html, unsafe_allow_html=True)

        buf = io.BytesIO()
        dff.to_csv(buf, index=False)
        st.download_button("Exportar CSV", buf.getvalue(),
                           "correspondentes.csv", "text/csv")

# ── EDITAR / EXCLUIR ───────────────────────────────────────────────────────
elif pagina == "Editar/Excluir":
    st.subheader("Editar ou Excluir Registro")
    df = load_data()
    if df.empty:
        st.info("Nenhum registro para editar.")
    else:
        opcoes = {f"{r.get('id')} - {r.get('nome','')}": r.get("id")
                  for _, r in df.iterrows()}
        sel = st.selectbox("Selecionar registro", list(opcoes.keys()))
        reg_id = opcoes[sel]
        reg    = df[df["id"] == reg_id].iloc[0].to_dict()

        tab_editar, tab_excluir = st.tabs(["Editar", "Excluir"])

        with tab_editar:
            with st.form("form_editar"):
                e1, e2 = st.columns(2)
                nome_e     = e1.text_input("Nome *",          value=reg.get("nome",""))
                oab_e      = e2.text_input("OAB",             value=reg.get("oab","") or "")
                telefone_e = e1.text_input("Telefone",        value=reg.get("telefone","") or "")
                cidade_e   = e2.text_input("Cidade",          value=reg.get("cidade","") or "")
                est_idx    = ESTADOS.index(reg.get("estado","")) if reg.get("estado") in ESTADOS else 0
                estado_e   = e1.selectbox("Estado", ESTADOS,  index=est_idx)
                empresa_e  = e2.text_input("Empresa",         value=reg.get("empresa","") or "")
                cliente_e  = e1.text_input("Cliente",         value=reg.get("cliente","") or "")
                tipo_idx   = TIPOS.index(reg.get("tipo",""))  if reg.get("tipo") in TIPOS else 0
                tipo_e     = e2.selectbox("Tipo de Servico", TIPOS, index=tipo_idx)
                try:
                    data_val = date.fromisoformat(str(reg.get("data","")))
                except Exception:
                    data_val = date.today()
                data_e     = e1.date_input("Data do Servico", value=data_val)
                pagamento_e= e2.text_input("Pagamento",       value=reg.get("pagamento","") or "")
                obs_e      = st.text_area("Observacoes",      value=reg.get("obs","") or "", height=80)
                etiqueta_idx_e = ETIQUETAS.index(reg.get("etiqueta","")) if reg.get("etiqueta") in ETIQUETAS else 0
                etiqueta_e   = st.selectbox("Etiqueta", ETIQUETAS, index=etiqueta_idx_e)
                if etiqueta_e:
                    cor_e = ETIQUETAS_CORES.get(etiqueta_e, "#cccccc")
                    st.markdown(f'<div style="display:inline-block;background:{cor_e};color:white;padding:4px 14px;border-radius:12px;font-weight:600;">{etiqueta_e}</div>', unsafe_allow_html=True)
                salvar   = st.form_submit_button("Salvar Alteracoes", use_container_width=True)

            if salvar:
                if not nome_e:
                    st.error("O campo Nome e obrigatorio.")
                else:
                    upd = {
                        "nome":      nome_e,
                        "oab":       oab_e      if oab_e      else None,
                        "telefone":  telefone_e if telefone_e else None,
                        "cidade":    cidade_e   if cidade_e   else None,
                        "estado":    estado_e   if estado_e   else None,
                        "empresa":   empresa_e  if empresa_e  else None,
                        "cliente":   cliente_e  if cliente_e  else None,
                        "data":      str(data_e),
                        "tipo":      tipo_e     if tipo_e     else None,
                        "pagamento": pagamento_e if pagamento_e else None,
                        "obs":       obs_e      if obs_e      else None,
                        "etiqueta": etiqueta_e if etiqueta_e else None,
                    }
                    if update_data(reg_id, upd):
                        st.success("Registro atualizado!")
                        st.cache_data.clear()

        with tab_excluir:
            st.warning(f"Voce esta prestes a excluir o registro de **{reg.get('nome','')}**.")
            confirmar = st.checkbox("Sim, desejo excluir este registro", key="confirm_del")
            if st.button("Excluir Registro", disabled=not confirmar, type="primary", key="btn_del"):
                if delete_data(reg_id):
                    st.success("Registro excluido!")
                    st.cache_data.clear()


# ── GESTÃO FINANCEIRA ──────────────────────────────────────────
elif pagina == "Gestão Financeira":
    st.subheader("Gestão Financeira de Audiências")

    COLUNAS_FIN = [
        "Data", "Hora de Início", "ID", "Natureza", "Número CNJ",
        "Tipo / Subtipo", "Descrição", "Responsável pela Audiência", "Valor",
        "Cliente", "Parte Contrária", "Modalidade", "Solicitação", "Local",
        "Cidade", "UF", "Preposto", "Dados dos Correspondentes",
        "Classificação do Processo", "Observações", "Empresa Contratada",
        "Arquivo de Origem",
    ]
    # Colunas exibidas na prévia da importação (apenas estas)
    COLS_PREVIA = [
        "Data/Hora de Início", "Natureza", "Tipo / Subtipo",
        "Responsável pela Audiência", "Valor", "Cliente", "Parte Contrária",
        "Cidade", "UF", "Classificação do Processo", "Empresa Contratada",
    ]
    MAPA_DB = {
        "Data": "data", "Hora de Início": "hora_inicio", "ID": "id_audiencia",
        "Natureza": "natureza", "Número CNJ": "numero_cnj", "Tipo / Subtipo": "tipo_subtipo",
        "Descrição": "descricao", "Responsável pela Audiência": "responsavel", "Valor": "valor",
        "Cliente": "cliente", "Parte Contrária": "parte_contraria", "Modalidade": "modalidade",
        "Solicitação": "solicitacao", "Local": "local", "Cidade": "cidade", "UF": "uf",
        "Preposto": "preposto", "Dados dos Correspondentes": "dados_correspondentes",
        "Classificação do Processo": "classificacao_processo", "Observações": "observacoes",
        "Empresa Contratada": "empresa_contratada", "Arquivo de Origem": "arquivo_origem",
    }

    def parte_data(serie):
        # source pode vir ISO (2025-04-07 10:50:00) ou dd/mm/aaaa; tenta ISO primeiro
        dt = pd.to_datetime(serie, errors="coerce")
        falta = dt.isna()
        if falta.any():
            dt2 = pd.to_datetime(serie.where(falta), errors="coerce", dayfirst=True)
            dt = dt.fillna(dt2)
        return dt.dt.strftime("%d/%m/%Y"), dt.dt.strftime("%Hh%M"), dt, dt.dt.strftime("%Y-%m-%d")

    def fmt_brl(v):
        return "R$ " + ("%0.2f" % float(v or 0)).replace(",", "X").replace(".", ",").replace("X", ".")

    # ── Carrega lançamentos salvos no Supabase ──
    df_db = load_audiencias()
    if not df_db.empty:
        inv = {v: k for k, v in MAPA_DB.items()}
        df_fin = df_db.rename(columns=inv)
        for c in COLUNAS_FIN:
            if c not in df_fin.columns:
                df_fin[c] = ""
    else:
        df_fin = pd.DataFrame(columns=COLUNAS_FIN)

    if not df_fin.empty:
        df_fin["_dt"] = pd.to_datetime(df_fin["Data"], errors="coerce", dayfirst=True)
        df_fin["_cli_canon"] = df_fin["Cliente"].apply(cliente_canonico)
        df_fin["_valor_num"] = pd.to_numeric(df_fin["Valor"], errors="coerce").fillna(0.0)
    else:
        df_fin["_dt"] = pd.NaT
        df_fin["_cli_canon"] = ""
        df_fin["_valor_num"] = 0.0

    # ── Filtros (iniciam no mês vigente) ──
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)
    st.markdown("#### Lançamentos de audiências")
    f1, f2, f3 = st.columns(3)
    data_ini = f1.date_input("Data início", value=primeiro_dia_mes, key="fin_f_ini", format="DD/MM/YYYY")
    data_fim = f2.date_input("Data fim", value=hoje, key="fin_f_fim", format="DD/MM/YYYY")
    # Clientes agrupados por nome canônico (sem repetição)
    clientes_canon = sorted([x for x in df_fin["_cli_canon"].dropna().unique() if x]) if not df_fin.empty else []
    filtro_clientes = f3.multiselect("Cliente (um ou mais)", clientes_canon, key="fin_f_cliente")
    f4, f5, f6, f7 = st.columns(4)
    modal_opts = sorted([x for x in df_fin["Modalidade"].dropna().unique() if str(x).strip()]) if not df_fin.empty else []
    filtro_modal = f4.multiselect("Modalidade", modal_opts, key="fin_f_modal")
    emp_opts = sorted([x for x in df_fin["Empresa Contratada"].dropna().unique() if str(x).strip()]) if not df_fin.empty else []
    filtro_emp = f5.multiselect("Empresa Contratada", emp_opts, key="fin_f_emp")
    sol_opts = sorted([x for x in df_fin["Solicitação"].dropna().unique() if str(x).strip()]) if not df_fin.empty else []
    filtro_sol = f6.multiselect("Solicitação", sol_opts, key="fin_f_sol")
    clas_opts = sorted([x for x in df_fin["Classificação do Processo"].dropna().unique() if str(x).strip()]) if not df_fin.empty else []
    filtro_clas = f7.multiselect("Classificação do Processo", clas_opts, key="fin_f_clas")

    # ── Aplica filtros (período sempre ativo; default = mês vigente) ──
    dff = df_fin.copy()
    for c in dff.columns:
        if dff[c].dtype == object:
            dff[c] = dff[c].fillna("")
    if data_ini and data_fim and "_dt" in dff.columns and not dff.empty:
        ini_ts = pd.Timestamp(data_ini)
        fim_ts = pd.Timestamp(data_fim) + pd.Timedelta(days=1)
        dff = dff[(dff["_dt"] >= ini_ts) & (dff["_dt"] < fim_ts)]
    if filtro_clientes:
        dff = dff[dff["_cli_canon"].isin(filtro_clientes)]
    if filtro_modal:
        dff = dff[dff["Modalidade"].isin(filtro_modal)]
    if filtro_emp:
        dff = dff[dff["Empresa Contratada"].isin(filtro_emp)]
    if filtro_sol:
        dff = dff[dff["Solicitação"].isin(filtro_sol)]
    if filtro_clas:
        dff = dff[dff["Classificação do Processo"].isin(filtro_clas)]

    # ── Indicadores e gráficos (refletem o filtro de data; default mês vigente) ──
    total_contratado = float(dff["_valor_num"].sum()) if not dff.empty else 0.0
    qtd_lanc = len(dff)
    meses_pt = ["janeiro","fevereiro","março","abril","maio","junho","julho",
                "agosto","setembro","outubro","novembro","dezembro"]
    if data_ini and data_fim:
        legenda = f"{data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
    else:
        legenda = f"{meses_pt[hoje.month-1]}/{hoje.year}"

    cm1, cm2 = st.columns(2)
    cm1.markdown(f'<div class="metric-card"><h3>{fmt_brl(total_contratado)}</h3><p>Total Contratado ({legenda})</p></div>', unsafe_allow_html=True)
    cm2.markdown(f'<div class="metric-card"><h3>{qtd_lanc}</h3><p>Lançamentos no período</p></div>', unsafe_allow_html=True)

    if dff.empty:
        st.info("Sem dados no período/filtros selecionados. Ajuste o filtro de data (padrão: mês vigente) ou importe uma planilha.")
    else:
        PALETA = [COR_VERMELHO, COR_DOURADO, COR_DESTAQUE, "#D2691E", "#8B4513", "#5C1010"]
        ALT_GRAF = 260
        g1, g2 = st.columns(2)
        # Total por Cliente (10 maiores) — por quantidade de atividades
        tc = dff.groupby("_cli_canon").size().reset_index(name="Quantidade")
        tc.columns = ["Cliente", "Quantidade"]
        tc = tc[tc["Quantidade"] > 0].sort_values("Quantidade", ascending=False).head(10)
        if not tc.empty:
            fig_tc = px.bar(tc, x="Quantidade", y="Cliente", orientation="h",
                            title="Total por Cliente (10 maiores)", text_auto=True,
                            color_discrete_sequence=[COR_VERMELHO])
            fig_tc.update_layout(yaxis={"categoryorder": "total ascending"}, height=ALT_GRAF,
                                 margin=dict(l=10, r=10, t=40, b=10))
            g1.plotly_chart(fig_tc, use_container_width=True)
        # Total de contratações por mês — por quantidade de atividades
        vc = dff.dropna(subset=["_dt"]).copy()
        if not vc.empty:
            vc["MesData"] = vc["_dt"].dt.to_period("M").dt.to_timestamp()
            vc = vc.groupby("MesData").size().reset_index(name="Quantidade")
            vc.columns = ["MesData", "Quantidade"]
            vc = vc.sort_values("MesData")
            vc["Mês"] = vc["MesData"].dt.strftime("%m/%Y")
            fig_vc = px.bar(vc, x="Mês", y="Quantidade",
                            title="Total de contratações por mês", text_auto=True,
                            color_discrete_sequence=[COR_DOURADO])
            fig_vc.update_xaxes(type="category")
            fig_vc.update_layout(height=ALT_GRAF, margin=dict(l=10, r=10, t=40, b=10))
            g2.plotly_chart(fig_vc, use_container_width=True)

        g3, g4 = st.columns(2)
        # Empresa Contratada — por valor contratado
        ec = dff.groupby("Empresa Contratada")["_valor_num"].sum().reset_index()
        ec.columns = ["Empresa", "Total"]
        ec = ec[(ec["Empresa"].astype(str).str.strip() != "") & (ec["Total"] > 0)].sort_values("Total", ascending=False).head(15)
        if not ec.empty:
            fig_ec = px.bar(ec, x="Empresa", y="Total",
                            title="Empresa Contratada", text_auto=".2s",
                            color_discrete_sequence=[COR_DESTAQUE])
            fig_ec.update_layout(height=ALT_GRAF, margin=dict(l=10, r=10, t=40, b=10))
            g3.plotly_chart(fig_ec, use_container_width=True)
        # Total por Estado — por quantidade de atividades
        te = dff.groupby("UF").size().reset_index(name="Quantidade")
        te.columns = ["UF", "Quantidade"]
        te = te[(te["UF"].astype(str).str.strip() != "") & (te["Quantidade"] > 0)].sort_values("Quantidade", ascending=False)
        if not te.empty:
            fig_te = px.bar(te, x="UF", y="Quantidade",
                            title="Total por Estado", text_auto=True,
                            color_discrete_sequence=[COR_VERMELHO])
            fig_te.update_layout(height=ALT_GRAF, margin=dict(l=10, r=10, t=40, b=10))
            g4.plotly_chart(fig_te, use_container_width=True)
        # Total por Cidade (15 maiores) — por quantidade de atividades
        tcid = dff.groupby("Cidade").size().reset_index(name="Quantidade")
        tcid.columns = ["Cidade", "Quantidade"]
        tcid = tcid[(tcid["Cidade"].astype(str).str.strip() != "") & (tcid["Quantidade"] > 0)].sort_values("Quantidade", ascending=False).head(15)
        if not tcid.empty:
            fig_tcid = px.bar(tcid, x="Cidade", y="Quantidade",
                              title="Total por Cidade (15 maiores)", text_auto=True,
                              color_discrete_sequence=[COR_DOURADO])
            fig_tcid.update_layout(height=ALT_GRAF, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_tcid, use_container_width=True)

    st.markdown("---")

    # ── Importação de planilha (salva no Supabase para pesquisa posterior) ──
    st.markdown("#### Importar planilha de audiências")
    st.caption("Carregamento em massa — arquivos .xlsx ou .csv. A primeira linha deve conter os cabeçalhos das colunas.")
    arq_fin = st.file_uploader("Enviar planilha financeira", type=["csv", "xlsx", "xls"], key="fin_upload")

    COLS_MODELO = ["Data/Hora de Início", "ID", "Natureza", "Número CNJ", "Tipo / Subtipo",
                   "Descrição", "Responsável pela Audiência", "Valor", "Cliente", "Parte Contrária",
                   "Modalidade", "Solicitação", "Local", "Cidade", "UF", "Preposto",
                   "Dados dos Correspondentes", "Classificação do Processo", "Observações",
                   "Empresa Contratada", "Arquivo de Origem"]
    buf_modelo = io.BytesIO()
    pd.DataFrame(columns=COLS_MODELO).to_excel(buf_modelo, index=False, engine="openpyxl")
    st.download_button("Baixar modelo de planilha", buf_modelo.getvalue(),
                       "modelo_audiencias.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="fin_modelo")

    if arq_fin is not None:
        try:
            if arq_fin.name.endswith(".csv"):
                df_novo = pd.read_csv(arq_fin, dtype=str)
            else:
                # Lê a aba "Consolidado" quando existir; caso contrário, a primeira
                xls = pd.ExcelFile(arq_fin)
                aba = "Consolidado" if "Consolidado" in xls.sheet_names else xls.sheet_names[0]
                df_novo = pd.read_excel(xls, sheet_name=aba, dtype=str)
            df_novo.columns = [str(c).strip() for c in df_novo.columns]

            col_dh = None
            for c in df_novo.columns:
                if c.lower().replace(" ", "") in ("data/horadeinício", "data/horadeinicio", "datahoradeinicio"):
                    col_dh = c
                    break
            if col_dh:
                d_fmt, h_fmt, _, iso_fmt = parte_data(df_novo[col_dh])
                df_novo["Data"] = d_fmt
                df_novo["Hora de Início"] = h_fmt
                df_novo["_data_iso"] = iso_fmt

            # ── Conferência e ajuste de inconsistências antes da importação ──
            st.write(f"Prévia e conferência dos dados ({len(df_novo)} linha(s)):")
            st.caption("Revise abaixo. Linhas com possíveis inconsistências estão sinalizadas. "
                       "Você pode corrigir qualquer célula diretamente na tabela antes de importar.")

            cols_conf = [c for c in COLS_PREVIA if c in df_novo.columns]
            for extra in ("Data", "Hora de Início", "Número CNJ"):
                if extra in df_novo.columns and extra not in cols_conf:
                    cols_conf.append(extra)
            if not cols_conf:
                cols_conf = list(df_novo.columns)

            df_conf = df_novo.copy()

            UFS_VALIDAS = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
                           "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}

            def checa_linha(row):
                probs = []
                dval = str(row.get("Data", "") or "").strip()
                if not dval:
                    probs.append("Data ausente")
                elif pd.isna(pd.to_datetime(dval, format="%d/%m/%Y", errors="coerce")):
                    probs.append("Data inválida")
                vraw = row.get("Valor")
                vtxt = str(vraw or "").strip()
                if vtxt and pd.isna(pd.to_numeric(pd.Series([vtxt.replace(".", "").replace(",", ".")]), errors="coerce").iloc[0]):
                    probs.append("Valor não numérico")
                if not str(row.get("Cliente", "") or "").strip():
                    probs.append("Cliente ausente")
                uf = str(row.get("UF", "") or "").strip().upper()
                if uf and uf not in UFS_VALIDAS:
                    probs.append("UF inválida")
                return "; ".join(probs)

            df_conf["Inconsistências"] = df_conf.apply(checa_linha, axis=1)
            n_inconsist = int((df_conf["Inconsistências"] != "").sum())

            if n_inconsist:
                st.warning(f"{n_inconsist} linha(s) com possíveis inconsistências. "
                           "Corrija na tabela abaixo (ou importe assim mesmo, se preferir).")
                with st.expander(f"Ver detalhes das {n_inconsist} inconsistência(s)"):
                    st.dataframe(df_conf.loc[df_conf["Inconsistências"] != "",
                                             [c for c in cols_conf if c in df_conf.columns] + ["Inconsistências"]],
                                 hide_index=True, use_container_width=True)
            else:
                st.success("Nenhuma inconsistência detectada na conferência inicial.")

            cols_editor = [c for c in cols_conf if c in df_conf.columns] + ["Inconsistências"]
            df_edit = st.data_editor(
                df_conf[cols_editor],
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                disabled=["Inconsistências"],
                key="fin_editor",
            )

            df_final = df_novo.copy()
            for c in cols_editor:
                if c != "Inconsistências" and c in df_edit.columns:
                    df_final[c] = df_edit[c].values

            restantes = int(df_edit.apply(checa_linha, axis=1).map(lambda s: 1 if s else 0).sum())
            if restantes:
                st.info(f"Ainda há {restantes} linha(s) com inconsistências. Você pode corrigir ou importar assim mesmo.")

            if st.button("Importar e salvar registros", type="primary", key="fin_salvar"):
                registros = []
                for _, row in df_final.iterrows():
                    rec = {}
                    for rotulo, col_db in MAPA_DB.items():
                        val = row.get(rotulo)
                        if col_db == "valor":
                            v = pd.to_numeric(pd.Series([val]), errors="coerce").iloc[0]
                            rec[col_db] = float(v) if pd.notna(v) else None
                        elif col_db == "data":
                            # Usa formato ISO para armazenamento confiável e filtragem
                            iso_val = row.get("_data_iso")
                            if pd.notna(iso_val) and str(iso_val).strip() not in ("", "NaT", "nan"):
                                rec[col_db] = str(iso_val).strip()
                            else:
                                rec[col_db] = (str(val).strip() if pd.notna(val) and str(val).strip() else None)
                        else:
                            rec[col_db] = (str(val).strip() if pd.notna(val) and str(val).strip() else None)
                    registros.append(rec)
                if registros:
                    sb = get_supabase()
                    total_ok = 0
                    erros = []
                    for i in range(0, len(registros), 200):
                        lote = registros[i:i+200]
                        try:
                            resp = sb.table("audiencias").insert(lote).execute()
                            total_ok += len(resp.data) if resp.data else 0
                        except Exception as e_lote:
                            erros.append(f"Lote {i}-{i+len(lote)}: {e_lote}")
                    st.cache_data.clear()
                    try:
                        chk = sb.table("audiencias").select("id", count="exact").execute()
                        total_banco = chk.count if getattr(chk, "count", None) is not None else "?"
                    except Exception:
                        total_banco = "?"
                    if erros:
                        st.error(f"Importados {total_ok} de {len(registros)}. Total no banco: {total_banco}. Erros: " + " | ".join(erros[:3]))
                    else:
                        st.success(f"{total_ok} registro(s) importado(s). Total no banco agora: {total_banco}.")
        except Exception as e:
            st.error(f"Erro ao processar a planilha: {e}")

    st.markdown("---")

    # ── Tabela de lançamentos com filtros aplicados ──
    st.write(f"**{len(dff)} lançamento(s) encontrado(s)**")
    cols_exibir = [c for c in COLUNAS_FIN if c in dff.columns]
    if dff.empty:
        st.info("Nenhum lançamento no período/filtros selecionados. Importe uma planilha ou ajuste os filtros.")
    else:
        st.dataframe(dff[cols_exibir], hide_index=True, use_container_width=True)
        # Exportação em Excel no padrão inicial (colunas da prévia)
        cols_export_base = ["Data", "Hora de Início"] + [c for c in COLS_PREVIA if c not in ("Data/Hora de Início",)]
        cols_export = [c for c in cols_export_base if c in dff.columns]
        df_export = dff[cols_export].copy()
        buf_fin = io.BytesIO()
        with pd.ExcelWriter(buf_fin, engine="xlsxwriter") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Lançamentos")
            wb = writer.book
            ws = writer.sheets["Lançamentos"]
            fmt_cab = wb.add_format({"bold": True, "bg_color": "#8B1A1A", "font_color": "#FFFFFF", "border": 1, "align": "center", "valign": "vcenter"})
            for col_idx, nome in enumerate(df_export.columns):
                ws.write(0, col_idx, nome, fmt_cab)
                serie_txt = df_export[nome].astype(str)
                max_val = serie_txt.str.len().max()
                max_len = int(max_val) if pd.notna(max_val) else 0
                larg = max(len(str(nome)), max_len) + 2
                ws.set_column(col_idx, col_idx, min(larg, 45))
            ws.freeze_panes(1, 0)
        st.download_button("Exportar Excel", buf_fin.getvalue(),
                           "gestao_financeira.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="fin_export")
