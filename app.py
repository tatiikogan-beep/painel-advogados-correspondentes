import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import plotly.express as px

st.set_page_config(
    page_title="Painel – Advogados Correspondentes",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
div[data-testid="stMetric"] {
    background: white; border-radius: 10px; padding: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,.08); border-top: 4px solid #3949ab;
}
</style>
""", unsafe_allow_html=True)

DATA_FILE = "dados.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

if "registros" not in st.session_state:
    st.session_state.registros = load_data()

ESTADOS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
           "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
TIPOS = ["Conciliação","Instrução","Inicial","UNA"]
STATUS_PAG = ["Pendente","Pago","Parcial"]

st.markdown("""
<div style='background:linear-gradient(135deg,#1a237e,#283593);color:white;
padding:18px 24px;border-radius:10px;margin-bottom:24px;text-align:center'>
<h1 style='margin:0;font-size:1.8rem'>⚖️ Painel – Advogados Correspondentes</h1>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("📌 Navegação")
pagina = st.sidebar.radio("", ["📊 Dashboard","➕ Cadastro","📋 Registros","✏️ Editar/Excluir"])
st.sidebar.markdown("---")
st.sidebar.info(f"**Total de registros:** {len(st.session_state.registros)}")

# ── DASHBOARD ────────────────────────────────────────────────────────────────
if pagina == "📊 Dashboard":
    st.subheader("📊 Visão Geral")
    registros = st.session_state.registros
    df = pd.DataFrame(registros) if registros else pd.DataFrame()
    hoje = date.today()
    prox30 = hoje + timedelta(days=30)
    total = len(registros)
    if not df.empty and "data" in df.columns:
        df["data_dt"] = pd.to_datetime(df["data"], errors="coerce")
        futuras = df[(df["data_dt"].dt.date >= hoje) & (df["data_dt"].dt.date <= prox30)]
        n_fut   = len(futuras)
        n_conc  = len(df[df["tipo"]=="Conciliação"]) if "tipo" in df.columns else 0
        n_instr = len(df[df["tipo"]=="Instrução"])   if "tipo" in df.columns else 0
        n_pago  = len(df[df["pagamento"]=="Pago"])   if "pagamento" in df.columns else 0
    else:
        n_fut = n_conc = n_instr = n_pago = 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("👥 Total",             total)
    c2.metric("📅 Próx. 30 dias",     n_fut)
    c3.metric("🤝 Conciliações",      n_conc)
    c4.metric("📖 Instruções",        n_instr)
    c5.metric("💰 Pagos",             n_pago)

    if not df.empty and "tipo" in df.columns:
        st.markdown("---")
        col1,col2 = st.columns(2)
        with col1:
            fig = px.pie(df, names="tipo", title="Audiências por Tipo",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            if "estado" in df.columns:
                cnt = df["estado"].value_counts().reset_index()
                cnt.columns = ["Estado","Qtd"]
                fig2 = px.bar(cnt, x="Estado", y="Qtd", title="Por Estado",
                              color="Qtd", color_continuous_scale="Blues")
                fig2.update_layout(height=320)
                st.plotly_chart(fig2, use_container_width=True)

        col3,col4 = st.columns(2)
        with col3:
            if "cliente" in df.columns:
                cnt2 = df["cliente"].value_counts().head(10).reset_index()
                cnt2.columns = ["Cliente","Qtd"]
                fig3 = px.bar(cnt2, x="Qtd", y="Cliente", orientation="h",
                              title="Top 10 Clientes", color="Qtd",
                              color_continuous_scale="Greens")
                fig3.update_layout(height=320)
                st.plotly_chart(fig3, use_container_width=True)
        with col4:
            if "data_dt" in df.columns:
                df["mes"] = df["data_dt"].dt.to_period("M").astype(str)
                cnt3 = df["mes"].value_counts().sort_index().reset_index()
                cnt3.columns = ["Mês","Qtd"]
                fig4 = px.line(cnt3, x="Mês", y="Qtd", title="Audiências por Mês", markers=True)
                fig4.update_layout(height=320)
                st.plotly_chart(fig4, use_container_width=True)

        st.markdown("### 📅 Próximas Audiências (30 dias)")
        if n_fut > 0:
            cols_s = [c for c in ["nome","cliente","cidade","estado","tipo","data"] if c in futuras.columns]
            st.dataframe(futuras[cols_s].sort_values("data"), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma audiência nos próximos 30 dias.")
    else:
        st.info("Nenhum dado cadastrado. Vá para ➕ Cadastro.")

# ── CADASTRO ─────────────────────────────────────────────────────────────────
elif pagina == "➕ Cadastro":
    st.subheader("➕ Novo Correspondente / Audiência")
    with st.form("form_cad", clear_on_submit=True):
        st.markdown("**Dados do Advogado**")
        a1,a2,a3 = st.columns(3)
        nome     = a1.text_input("Nome Completo *")
        telefone = a2.text_input("Telefone *")
        oab      = a3.text_input("OAB *")

        st.markdown("**Localização**")
        b1,b2 = st.columns([3,1])
        cidade = b1.text_input("Cidade *")
        estado = b2.selectbox("Estado *", [""]+ESTADOS)

        st.markdown("**Audiência**")
        d1,d2,d3 = st.columns(3)
        cliente  = d1.text_input("Cliente *")
        data_aud = d2.date_input("Data *", value=date.today())
        tipo     = d3.selectbox("Tipo *", [""]+TIPOS)

        st.markdown("**Detalhes**")
        e1,e2,e3 = st.columns(3)
        forum    = e1.text_input("Fórum")
        processo = e2.text_input("Nº Processo")
        area     = e3.text_input("Área Jurídica")

        f1,f2 = st.columns(2)
        honorarios = f1.number_input("Honorários (R$)", min_value=0.0, step=50.0, format="%.2f")
        pagamento  = f2.selectbox("Status Pagamento", [""]+STATUS_PAG)

        obs = st.text_area("Observações")

        st.markdown("**Campos Personalizados**")
        n_extras = st.number_input("Qtd. campos extras:", min_value=0, max_value=10, value=0, step=1)
        extras = []
        for i in range(int(n_extras)):
            g1,g2 = st.columns(2)
            k = g1.text_input(f"Campo {i+1}", key=f"ek{i}")
            v = g2.text_input(f"Valor {i+1}",  key=f"ev{i}")
            if k: extras.append({"chave":k,"valor":v})

        ok = st.form_submit_button("💾 Salvar", type="primary", use_container_width=True)

    if ok:
        erros = [f for f,v in [("Nome",nome),("Telefone",telefone),("OAB",oab),
                                ("Cidade",cidade),("Estado",estado),("Cliente",cliente),("Tipo",tipo)] if not v]
        if erros:
            st.error(f"Campos obrigatórios: {', '.join(erros)}")
        else:
            reg = {"id":int(datetime.now().timestamp()*1000),"nome":nome,"telefone":telefone,
                   "oab":oab,"cidade":cidade,"estado":estado,"cliente":cliente,"data":str(data_aud),
                   "tipo":tipo,"forum":forum,"processo":processo,"area":area,
                   "honorarios":honorarios,"pagamento":pagamento,"obs":obs,"extras":extras,
                   "criado_em":datetime.now().isoformat()}
            st.session_state.registros.append(reg)
            save_data(st.session_state.registros)
            st.success("✅ Salvo com sucesso!")
            st.balloons()

# ── REGISTROS ────────────────────────────────────────────────────────────────
elif pagina == "📋 Registros":
    st.subheader("📋 Consultar Registros")
    registros = st.session_state.registros
    if not registros:
        st.info("Nenhum registro. Cadastre o primeiro!")
    else:
        df = pd.DataFrame(registros)
        st.markdown("**🔍 Filtros**")
        h1,h2,h3,h4,h5 = st.columns(5)
        fn = h1.text_input("Nome")
        fc = h2.text_input("Cliente")
        fe = h3.selectbox("Estado", ["Todos"]+ESTADOS)
        ft = h4.selectbox("Tipo",   ["Todos"]+TIPOS)
        fo = h5.text_input("OAB")

        mask = pd.Series([True]*len(df))
        if fn: mask &= df["nome"].str.contains(fn, case=False, na=False)
        if fc: mask &= df["cliente"].str.contains(fc, case=False, na=False)
        if fe != "Todos": mask &= df["estado"]==fe
        if ft != "Todos": mask &= df["tipo"]==ft
        if fo: mask &= df["oab"].str.contains(fo, case=False, na=False)

        df_f = df[mask].copy()
        st.markdown(f"**{len(df_f)} de {len(df)} registros**")
        cols_s = [c for c in ["nome","oab","telefone","cidade","estado","cliente","data","tipo","pagamento"] if c in df_f.columns]
        st.dataframe(df_f[cols_s].sort_values("data",ascending=False), use_container_width=True, hide_index=True)
        csv = df_f.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("📥 Exportar CSV", data=csv,
                           file_name=f"correspondentes_{date.today()}.csv", mime="text/csv", type="primary")

# ── EDITAR / EXCLUIR ─────────────────────────────────────────────────────────
elif pagina == "✏️ Editar/Excluir":
    st.subheader("✏️ Editar ou Excluir Registro")
    registros = st.session_state.registros
    if not registros:
        st.info("Nenhum registro.")
    else:
        nomes = [f"{r['nome']} | {r['cliente']} | {r['data']}" for r in registros]
        sel = st.selectbox("Registro:", nomes)
        idx = nomes.index(sel)
        r   = registros[idx]

        if st.button("🗑️ Excluir este registro", type="secondary"):
            if st.session_state.get("conf_del")==idx:
                st.session_state.registros.pop(idx)
                save_data(st.session_state.registros)
                st.success("Excluído!")
                st.session_state.conf_del=None
                st.rerun()
            else:
                st.session_state.conf_del=idx
                st.warning("Clique novamente para confirmar.")

        with st.form("form_edit"):
            i1,i2,i3 = st.columns(3)
            nome     = i1.text_input("Nome *",     value=r.get("nome",""))
            telefone = i2.text_input("Telefone *", value=r.get("telefone",""))
            oab      = i3.text_input("OAB *",      value=r.get("oab",""))
            j1,j2   = st.columns([3,1])
            cidade  = j1.text_input("Cidade *",    value=r.get("cidade",""))
            est_i   = ESTADOS.index(r["estado"]) if r.get("estado") in ESTADOS else 0
            estado  = j2.selectbox("Estado *", ESTADOS, index=est_i)
            k1,k2,k3 = st.columns(3)
            cliente = k1.text_input("Cliente *",   value=r.get("cliente",""))
            dv = datetime.strptime(r["data"],"%Y-%m-%d").date() if r.get("data") else date.today()
            data_aud = k2.date_input("Data *", value=dv)
            tip_i = TIPOS.index(r["tipo"]) if r.get("tipo") in TIPOS else 0
            tipo  = k3.selectbox("Tipo *", TIPOS, index=tip_i)
            l1,l2,l3 = st.columns(3)
            forum    = l1.text_input("Fórum",      value=r.get("forum",""))
            processo = l2.text_input("Processo",   value=r.get("processo",""))
            area     = l3.text_input("Área",       value=r.get("area",""))
            m1,m2   = st.columns(2)
            honorarios = m1.number_input("Honorários", value=float(r.get("honorarios",0) or 0), min_value=0.0, step=50.0, format="%.2f")
            pag_i = STATUS_PAG.index(r["pagamento"]) if r.get("pagamento") in STATUS_PAG else 0
            pagamento = m2.selectbox("Pagamento", STATUS_PAG, index=pag_i)
            obs = st.text_area("Observações", value=r.get("obs",""))
            if st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True):
                st.session_state.registros[idx].update({
                    "nome":nome,"telefone":telefone,"oab":oab,"cidade":cidade,"estado":estado,
                    "cliente":cliente,"data":str(data_aud),"tipo":tipo,"forum":forum,
                    "processo":processo,"area":area,"honorarios":honorarios,
                    "pagamento":pagamento,"obs":obs,"atualizado_em":datetime.now().isoformat()
                })
                save_data(st.session_state.registros)
                st.success("✅ Atualizado!")
                st.rerun()
