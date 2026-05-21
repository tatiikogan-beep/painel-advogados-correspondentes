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

PAGINAS = ["Dashboard", "Cadastro", "Importar Planilha", "Registros", "Editar/Excluir"]
st.sidebar.markdown('<p style="font-size:0.7rem;color:rgba(255,255,255,0.5);'
                    'margin-bottom:4px;">NAVEGACAO</p>', unsafe_allow_html=True)
pagina = st.sidebar.radio("", PAGINAS, label_visibility="collapsed")

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
                    "cliente","tipo","data","pagamento","obs"]
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
        col1, col2, col3 = st.columns(3)
        filtro_nome   = col1.text_input("Buscar por Nome")
        filtro_estado = col2.selectbox("Filtrar por Estado", [""] + ESTADOS[1:])
        filtro_cidade = col3.text_input("Filtrar por Cidade")

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

        st.write(f"**{len(dff)} registro(s) encontrado(s)**")
        st.dataframe(dff, hide_index=True, use_container_width=True)

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
                salvar     = st.form_submit_button("Salvar Alteracoes", use_container_width=True)

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
