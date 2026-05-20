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

COR_VERMELHO   = "#8B1A1A"
COR_DOURADO    = "#C8A951"
COR_BRANCO     = "#FFFFFF"
COR_CINZA_BG   = "#F5F5F5"
COR_DESTAQUE   = "#A52A2A"

def get_logo_b64():
    if os.path.isfile("logo.png"):
        return base64.b64encode(open("logo.png", "rb").read()).decode()
    return ""

st.markdown(f"""
<style>
.stApp {{ background-color: {COR_CINZA_BG}; }}
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {COR_VERMELHO} 0%, #5a1010 100%);
}}
section[data-testid="stSidebar"] * {{ color: {COR_BRANCO} !important; }}
section[data-testid="stSidebar"] .stRadio label {{ color: {COR_BRANCO} !important; }}
div[data-testid="stMetric"] {{
    background: {COR_BRANCO};
    border-radius: 10px;
    padding: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
    border-top: 4px solid {COR_DOURADO};
}}
div[data-testid="stMetricValue"] {{ color: {COR_VERMELHO} !important; }}
.stButton > button {{
    background: {COR_VERMELHO};
    color: {COR_BRANCO};
    border: none;
    border-radius: 6px;
    font-weight: 600;
}}
.stButton > button:hover {{ background: {COR_DESTAQUE}; color: {COR_BRANCO}; }}
.stTabs [data-baseweb="tab"] {{ color: {COR_VERMELHO}; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ border-bottom: 3px solid {COR_DOURADO} !important; }}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

def load_data():
    try:
        res = supabase.table("correspondentes").select("*").order("data", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def insert_data(record: dict):
    try:
        supabase.table("correspondentes").insert(record).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir: {e}")
        return False

def update_data(id_: int, record: dict):
    try:
        supabase.table("correspondentes").update(record).eq("id", id_).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False

def delete_data(id_: int):
    try:
        supabase.table("correspondentes").delete().eq("id", id_).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False

ESTADOS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
           "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
TIPOS = ["","Conciliacao","Instrucao","Inicial","UNA"]
STATUS_PAG = ["Pendente","Pago","Parcial"]

logo_b64 = get_logo_b64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:70px;vertical-align:middle;margin-right:16px;">' if logo_b64 else "\u2696\ufe0f"

st.markdown(f"""
<div style='background:linear-gradient(135deg,{COR_VERMELHO},{COR_DESTAQUE});
            color:{COR_BRANCO};padding:18px 24px;border-radius:10px;
            margin-bottom:24px;text-align:center;
            border-bottom:4px solid {COR_DOURADO};'>
  <div style='display:flex;align-items:center;justify-content:center;gap:16px;'>
    {logo_html}
    <div>
      <h1 style='margin:0;font-size:1.8rem;font-weight:700;'>Painel - Advogados Correspondentes</h1>
      <p style='margin:4px 0 0;font-size:0.9rem;opacity:0.85;'>Imaculada Gordiano Sociedade de Advogados</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

sidebar_logo = f'<img src="data:image/png;base64,{logo_b64}" style="width:120px;border-radius:8px;">' if logo_b64 else ""
st.sidebar.markdown(f"""
<div style='text-align:center;padding:12px 0 8px;'>
  {sidebar_logo}
  <p style='font-size:0.75rem;margin:6px 0 0;opacity:0.8;'>Imaculada Gordiano</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.title("\U0001f4cc Navegacao")
pagina = st.sidebar.radio("nav", ["\U0001f4ca Dashboard","\u2795 Cadastro","\U0001f4e6 Importar Planilha","\U0001f4cb Registros","\u270f\ufe0f Editar/Excluir"], label_visibility="collapsed")
st.sidebar.markdown("---")

registros = load_data()
st.sidebar.info(f"**Total de registros:** {len(registros)}")

if pagina == "\U0001f4ca Dashboard":
    st.subheader("Dashboard - Visao Geral")
    df = pd.DataFrame(registros) if registros else pd.DataFrame()
    hoje = date.today()
    prox30 = hoje + timedelta(days=30)
    total = len(registros)
    if not df.empty and "data" in df.columns:
        df["data_dt"] = pd.to_datetime(df["data"], errors="coerce")
        futuras = df[(df["data_dt"].dt.date >= hoje) & (df["data_dt"].dt.date <= prox30)]
        n_fut = len(futuras)
        n_conc = len(df[df["tipo"]=="Conciliacao"]) if "tipo" in df.columns else 0
        n_instr = len(df[df["tipo"]=="Instrucao"]) if "tipo" in df.columns else 0
        n_pago = len(df[df["pagamento"]=="Pago"]) if "pagamento" in df.columns else 0
    else:
        n_fut = n_conc = n_instr = n_pago = 0
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total", total)
    c2.metric("Prox. 30 dias", n_fut)
    c3.metric("Conciliacoes", n_conc)
    c4.metric("Instrucoes", n_instr)
    c5.metric("Pagos", n_pago)
    if not df.empty and "tipo" in df.columns:
        st.markdown("---")
        col1,col2 = st.columns(2)
        with col1:
            fig = px.pie(df, names="tipo", title="Audiencias por Tipo",
                         color_discrete_sequence=[COR_VERMELHO, COR_DOURADO, "#c0392b", "#e67e22"])
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "estado" in df.columns:
                fig2 = px.bar(df["estado"].value_counts().reset_index(),
                              x="estado", y="count", title="Audiencias por Estado",
                              color_discrete_sequence=[COR_DOURADO])
                fig2.update_layout(height=320)
                st.plotly_chart(fig2, use_container_width=True)
    if not df.empty and "pagamento" in df.columns:
        st.markdown("---")
        col3,col4 = st.columns(2)
        with col3:
            fig3 = px.pie(df, names="pagamento", title="Status de Pagamento",
                          color_discrete_sequence=[COR_VERMELHO, COR_DOURADO, "#888"])
            fig3.update_layout(height=320)
            st.plotly_chart(fig3, use_container_width=True)

elif pagina == "\u2795 Cadastro":
    st.subheader("Novo Cadastro")
    with st.form("form_cadastro", clear_on_submit=True):
        c1,c2,c3 = st.columns(3)
        nome = c1.text_input("Nome *")
        oab = c2.text_input("OAB *")
        telefone = c3.text_input("Telefone *")
        c4,c5,c6 = st.columns(3)
        cidade = c4.text_input("Cidade *")
        estado = c5.selectbox("Estado *", ESTADOS)
        empresa = c6.text_input("Empresa")
        c7,c8,c9 = st.columns(3)
        cliente = c7.text_input("Cliente *")
        data_aud = c8.date_input("Data da Audiencia *", value=date.today())
        tipo = c9.selectbox("Tipo", TIPOS)
        c10,c11 = st.columns(2)
        pagamento = c10.selectbox("Status Pagamento", STATUS_PAG)
        obs = c11.text_area("Observacoes", height=80)
        submitted = st.form_submit_button("Salvar", use_container_width=True)
    if submitted:
        erros = []
        if not nome: erros.append("Nome")
        if not oab: erros.append("OAB")
        if not telefone: erros.append("Telefone")
        if not cidade: erros.append("Cidade")
        if not cliente: erros.append("Cliente")
        if erros:
            st.error(f"Preencha os campos obrigatorios: {', '.join(erros)}")
        else:
            record = {
                "nome": nome, "oab": oab, "telefone": telefone,
                "cidade": cidade, "estado": estado,
                "empresa": empresa if empresa else None,
                "cliente": cliente, "data": str(data_aud),
                "tipo": tipo if tipo else None,
                "pagamento": pagamento,
                "obs": obs if obs else None,
            }
            if insert_data(record):
                st.success("Registro salvo com sucesso!")
                st.cache_data.clear()

elif pagina == "\U0001f4e6 Importar Planilha":
    st.subheader("Importacao em Lote - Planilha Excel")
    st.markdown(f"""
    <div style='background:{COR_BRANCO};border-left:5px solid {COR_DOURADO};padding:16px;border-radius:6px;margin-bottom:16px;'>
      <strong>Formato esperado da planilha Excel (.xlsx)</strong><br><br>
      Colunas na ordem (cabecalho na 1a linha):
      <ol>
        <li><code>nome</code> - Nome do advogado (obrigatorio)</li>
        <li><code>oab</code> - Numero da OAB (obrigatorio)</li>
        <li><code>telefone</code> - Telefone (obrigatorio)</li>
        <li><code>cidade</code> - Cidade (obrigatorio)</li>
        <li><code>estado</code> - Sigla do estado ex: SP (obrigatorio)</li>
        <li><code>empresa</code> - Nome da empresa (opcional)</li>
        <li><code>cliente</code> - Nome do cliente (obrigatorio)</li>
        <li><code>data</code> - Data da audiencia AAAA-MM-DD (obrigatorio)</li>
        <li><code>tipo</code> - Tipo: Conciliacao, Instrucao, Inicial ou UNA (opcional)</li>
        <li><code>pagamento</code> - Status: Pendente, Pago ou Parcial (opcional)</li>
        <li><code>obs</code> - Observacoes (opcional)</li>
      </ol>
    </div>
    """, unsafe_allow_html=True)
    modelo = pd.DataFrame(columns=["nome","oab","telefone","cidade","estado","empresa","cliente","data","tipo","pagamento","obs"])
    modelo.loc[0] = ["Maria Silva","SP12345","11999990000","Sao Paulo","SP","Escritorio ABC","Cliente Exemplo","2026-06-15","Conciliacao","Pendente",""]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        modelo.to_excel(writer, index=False, sheet_name="Correspondentes")
    buf.seek(0)
    st.download_button("Baixar Planilha Modelo", buf, file_name="modelo_correspondentes.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown("---")
    arquivo = st.file_uploader("Selecione a planilha Excel", type=["xlsx","xls"])
    if arquivo:
        try:
            df_import = pd.read_excel(arquivo, dtype=str)
            df_import.columns = [c.strip().lower() for c in df_import.columns]
            colunas_obrigatorias = ["nome","oab","telefone","cidade","estado","cliente","data"]
            faltando = [c for c in colunas_obrigatorias if c not in df_import.columns]
            if faltando:
                st.error(f"Colunas obrigatorias faltando: {', '.join(faltando)}")
            else:
                df_import = df_import.fillna("")
                st.write(f"**{len(df_import)} registros encontrados:**")
                st.dataframe(df_import, use_container_width=True)
                if st.button("Confirmar Importacao", use_container_width=True):
                    erros_import = []
                    sucessos = 0
                    for i, row in df_import.iterrows():
                        if not row.get("nome") or not row.get("oab") or not row.get("cliente"):
                            erros_import.append(f"Linha {i+2}: campos obrigatorios vazios")
                            continue
                        record = {
                            "nome": str(row.get("nome","")).strip(),
                            "oab": str(row.get("oab","")).strip(),
                            "telefone": str(row.get("telefone","")).strip(),
                            "cidade": str(row.get("cidade","")).strip(),
                            "estado": str(row.get("estado","")).strip(),
                            "empresa": str(row.get("empresa","")).strip() or None,
                            "cliente": str(row.get("cliente","")).strip(),
                            "data": str(row.get("data","")).strip(),
                            "tipo": str(row.get("tipo","")).strip() or None,
                            "pagamento": str(row.get("pagamento","Pendente")).strip() or "Pendente",
                            "obs": str(row.get("obs","")).strip() or None,
                        }
                        if insert_data(record):
                            sucessos += 1
                        else:
                            erros_import.append(f"Linha {i+2}: erro ao inserir")
                    st.cache_data.clear()
                    st.success(f"{sucessos} registros importados!")
                    if erros_import:
                        st.warning("Erros:\n" + "\n".join(erros_import))
        except Exception as e:
            st.error(f"Erro ao ler planilha: {e}")

elif pagina == "\U0001f4cb Registros":
    st.subheader("Lista de Registros")
    df = pd.DataFrame(registros) if registros else pd.DataFrame()
    with st.expander("Filtros", expanded=True):
        fc1,fc2,fc3,fc4,fc5 = st.columns(5)
        f_nome = fc1.text_input("Nome", key="f_nome")
        f_cliente = fc2.text_input("Cliente", key="f_cliente")
        f_estado = fc3.selectbox("Estado", ["Todos"]+ESTADOS, key="f_estado")
        f_tipo = fc4.selectbox("Tipo", ["Todos"]+[t for t in TIPOS if t], key="f_tipo")
        f_oab = fc5.text_input("OAB", key="f_oab")
    if not df.empty:
        if f_nome: df = df[df["nome"].str.contains(f_nome, case=False, na=False)]
        if f_cliente: df = df[df["cliente"].str.contains(f_cliente, case=False, na=False)]
        if f_estado != "Todos": df = df[df["estado"]==f_estado]
        if f_tipo != "Todos": df = df[df["tipo"]==f_tipo]
        if f_oab: df = df[df["oab"].str.contains(f_oab, case=False, na=False)]
        st.write(f"**{len(df)} de {len(registros)} registros**")
        colunas_show = [c for c in ["nome","oab","telefone","cidade","estado","empresa","cliente","data","tipo","pagamento","obs"] if c in df.columns]
        st.dataframe(df[colunas_show].reset_index(drop=True), use_container_width=True)
        csv = df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("Exportar CSV", csv, "correspondentes.csv", "text/csv")
    else:
        st.info("Nenhum registro encontrado.")

elif pagina == "\u270f\ufe0f Editar/Excluir":
    st.subheader("Editar / Excluir Registros")
    if not registros:
        st.info("Nenhum registro disponivel.")
    else:
        df_ed = pd.DataFrame(registros)
        busca = st.text_input("Buscar por nome ou OAB", key="busca_edit")
        if busca:
            mask = (df_ed["nome"].str.contains(busca, case=False, na=False) |
                    df_ed["oab"].str.contains(busca, case=False, na=False))
            df_ed = df_ed[mask]
        if df_ed.empty:
            st.warning("Nenhum registro encontrado.")
        else:
            opcoes = {f"{r['nome']} - OAB {r['oab']} (ID {r['id']})": r['id'] for _, r in df_ed.iterrows()}
            escolha = st.selectbox("Selecione o registro", list(opcoes.keys()), key="sel_reg")
            reg_id = opcoes[escolha]
            reg = next(r for r in registros if r["id"] == reg_id)
            tab_editar, tab_excluir = st.tabs(["Editar", "Excluir"])
            with tab_editar:
                with st.form("form_editar"):
                    e1,e2,e3 = st.columns(3)
                    nome_e = e1.text_input("Nome *", value=reg.get("nome",""))
                    oab_e = e2.text_input("OAB *", value=reg.get("oab",""))
                    telefone_e = e3.text_input("Telefone *", value=reg.get("telefone",""))
                    e4,e5,e6 = st.columns(3)
                    cidade_e = e4.text_input("Cidade *", value=reg.get("cidade",""))
                    estado_e = e5.selectbox("Estado *", ESTADOS,
                                           index=ESTADOS.index(reg["estado"]) if reg.get("estado") in ESTADOS else 0)
                    empresa_e = e6.text_input("Empresa", value=reg.get("empresa","") or "")
                    e7,e8,e9 = st.columns(3)
                    cliente_e = e7.text_input("Cliente *", value=reg.get("cliente",""))
                    try:
                        data_val = datetime.strptime(reg.get("data",""), "%Y-%m-%d").date()
                    except:
                        data_val = date.today()
                    data_e = e8.date_input("Data *", value=data_val)
                    tipo_idx = TIPOS.index(reg["tipo"]) if reg.get("tipo") in TIPOS else 0
                    tipo_e = e9.selectbox("Tipo", TIPOS, index=tipo_idx)
                    e10,e11 = st.columns(2)
                    pag_idx = STATUS_PAG.index(reg["pagamento"]) if reg.get("pagamento") in STATUS_PAG else 0
                    pagamento_e = e10.selectbox("Status Pagamento", STATUS_PAG, index=pag_idx)
                    obs_e = e11.text_area("Observacoes", value=reg.get("obs","") or "", height=80)
                    salvar = st.form_submit_button("Salvar Alteracoes", use_container_width=True)
                if salvar:
                    erros_e = []
                    if not nome_e: erros_e.append("Nome")
                    if not oab_e: erros_e.append("OAB")
                    if not telefone_e: erros_e.append("Telefone")
                    if not cidade_e: erros_e.append("Cidade")
                    if not cliente_e: erros_e.append("Cliente")
                    if erros_e:
                        st.error(f"Preencha os campos obrigatorios: {', '.join(erros_e)}")
                    else:
                        upd = {
                            "nome": nome_e, "oab": oab_e, "telefone": telefone_e,
                            "cidade": cidade_e, "estado": estado_e,
                            "empresa": empresa_e if empresa_e else None,
                            "cliente": cliente_e, "data": str(data_e),
                            "tipo": tipo_e if tipo_e else None,
                            "pagamento": pagamento_e,
                            "obs": obs_e if obs_e else None,
                        }
                        if update_data(reg_id, upd):
                            st.success("Registro atualizado!")
                            st.cache_data.clear()
            with tab_excluir:
                st.warning(f"Voce esta prestes a excluir o registro de **{reg.get('nome','')}**.")
                st.markdown("Esta acao **nao pode ser desfeita**.")
                confirmar = st.checkbox("Sim, desejo excluir este registro", key="confirm_del")
                if st.button("Excluir Registro", disabled=not confirmar, type="primary", key="btn_del"):
                    if delete_data(reg_id):
                        st.success("Registro excluido!")
                        st.cache_data.clear()
