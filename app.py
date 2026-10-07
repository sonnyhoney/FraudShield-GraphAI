import os
import glob
import json
import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
from google import genai
from dotenv import load_dotenv
from pyvis.network import Network
import streamlit.components.v1 as components

# Load environment variables
load_dotenv(override=True)

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+ssc://51204372.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "51204372")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="FraudShield | FinCrime Graph Intelligence",
    page_icon="🛡️",
    layout="wide"
)

# Custom Cyber-Forensics Dark Theme
st.markdown("""
<style>
    .main-title { font-size: 2.4rem !important; font-weight: 800; color: #FFFFFF; margin-bottom: 0px; }
    .sub-title { font-size: 1.1rem !important; font-weight: 500; color: #00d2ff; margin-bottom: 25px; }
    
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.2em; background-color: #ef4444; color: white; font-weight: 700; font-size: 1.05rem; border: none; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #dc2626; box-shadow: 0px 4px 14px rgba(239, 68, 68, 0.4); }
    
    .metric-card {
        background: linear-gradient(135deg, #111726 0%, #090d16 100%); padding: 16px 20px; border-radius: 12px; border-left: 4px solid #ef4444; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .metric-title { font-size: 0.8rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 1.35rem; color: #FFFFFF; font-weight: 800; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONNECTORS & RESOURCE CACHING
# ==========================================
@st.cache_resource
def get_neo4j_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        max_connection_lifetime=30,
        liveness_check_timeout=10
    )

driver = get_neo4j_driver()

def get_gemini_client():
    if GEMINI_API_KEY:
        return genai.Client(api_key=GEMINI_API_KEY)
    return None

def cleanup_temp_files():
    for temp_file in glob.glob("temp_fincrime_*.html"):
        try:
            os.remove(temp_file)
        except Exception:
            pass

# ==========================================
# GRAPH QUERIES & FORENSIC SCANNERS
# ==========================================
def scan_circular_rings():
    """Detects cycles of funds transferred in closed loops."""
    cypher = """
    MATCH path = (a:Account)-[r:TRANSFERS_TO*3..6]->(a)
    WITH path, [n IN nodes(path) | n.account_number] AS cycle_accounts,
         reduce(total = 0, rel IN relationships(path) | total + rel.amount) AS total_flow,
         length(path) AS hop_count
    RETURN DISTINCT cycle_accounts, total_flow, hop_count
    ORDER BY total_flow DESC
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(cypher)
        return [dict(record) for record in result]

def scan_synthetic_device_farms():
    """Detects multiple distinct accounts sharing hardware IMEI and IP addresses."""
    cypher = """
    MATCH (c:Customer)-[:OWNS_ACCOUNT]->(a:Account)-[:LOGGED_IN_FROM]->(d:Device)-[:ROUTED_THROUGH]->(ip:IPAddress)
    WITH d, ip, collect(DISTINCT a.account_number) AS linked_accounts, collect(DISTINCT c.name) AS linked_customers
    WHERE size(linked_accounts) > 2
    RETURN d.device_id AS device_id, d.type AS device_type, d.os AS os, d.imei AS imei,
           ip.ip AS ip_address, ip.country AS ip_country, ip.is_vpn AS is_vpn,
           linked_accounts, linked_customers, size(linked_accounts) AS farm_size
    ORDER BY farm_size DESC
    """
    with driver.session() as session:
        result = session.run(cypher)
        return [dict(record) for record in result]

def scan_smurfing_mule_networks():
    """Detects structured deposits (under $10k) funneling from multiple mules to a kingpin."""
    cypher = """
    MATCH (mule_cust:Customer)-[:OWNS_ACCOUNT]->(mule:Account)-[r:TRANSFERS_TO]->(kingpin:Account)<-[:OWNS_ACCOUNT]-(kp_cust:Customer)
    WHERE r.amount >= 9000 AND r.amount < 10000
    WITH kingpin, kp_cust, 
         collect({mule_acc: mule.account_number, mule_name: mule_cust.name, amount: r.amount, tx_id: r.transaction_id, time: r.timestamp}) AS deposits,
         count(mule) AS mule_count,
         sum(r.amount) AS total_funneled
    WHERE mule_count >= 3
    RETURN kingpin.account_number AS kingpin_account, kp_cust.name AS kingpin_name, 
           total_funneled, mule_count, deposits
    ORDER BY total_funneled DESC
    """
    with driver.session() as session:
        result = session.run(cypher)
        return [dict(record) for record in result]

# ==========================================
# INTERACTIVE PYVIS FORENSIC TOPOLOGY
# ==========================================
def render_fincrime_subgraph(highlight_type="ALL"):
    net = Network(height="500px", width="100%", bgcolor="#090d16", font_color="#cbd5e1")
    net.force_atlas_2based()
    
    with driver.session() as session:
        # 1. Fetch Accounts & Customers
        accounts = session.run("MATCH (c:Customer)-[:OWNS_ACCOUNT]->(a:Account) RETURN c.name AS cust_name, c.risk_rating AS risk, a.account_number AS acc, a.type AS acc_type, a.flag AS flag")
        for r in accounts:
            acc = str(r["acc"])
            cust = str(r["cust_name"])
            flag = str(r["flag"])
            
            if "CYC" in acc or "INVESTIGATION" in flag:
                color = "#ef4444" # Red for laundering ring
                size = 22
                label = f"🚨 {acc}\n({cust})"
            elif "FARM" in acc:
                color = "#a855f7" # Purple for device farm
                size = 18
                label = f"📱 {acc}\n({cust})"
            elif "KINGPIN" in acc:
                color = "#f59e0b" # Amber for Kingpin
                size = 26
                label = f"👑 {acc}\n({cust})"
            elif "MULE" in acc:
                color = "#3b82f6" # Blue for Mules
                size = 15
                label = f"🐟 {acc}"
            else:
                color = "#10b981" # Green for Clean
                size = 14
                label = f"✅ {acc}"
                
            net.add_node(acc, label=label, color=color, size=size, font={"color": "white", "size": 10})

        # 2. Fetch Devices & IPs
        devices = session.run("MATCH (a:Account)-[:LOGGED_IN_FROM]->(d:Device)-[:ROUTED_THROUGH]->(ip:IPAddress) RETURN a.account_number AS acc, d.device_id AS dev, ip.ip AS ip")
        for r in devices:
            acc, dev, ip = str(r["acc"]), str(r["dev"]), str(r["ip"])
            net.add_node(dev, label=f"🖥️ {dev}", color="#6366f1", size=16, font={"color": "#c7d2fe", "size": 9})
            net.add_node(ip, label=f"🌐 {ip}\n[VPN]", color="#ec4899", size=14, font={"color": "#fbcfe8", "size": 9})
            net.add_edge(acc, dev, title="LOGGED_IN_FROM", color="#475569", width=1)
            net.add_edge(dev, ip, title="ROUTED_THROUGH", color="#ec4899", width=1)

        # 3. Fetch Financial Transfers
        transfers = session.run("MATCH (src:Account)-[r:TRANSFERS_TO]->(dst:Account) RETURN src.account_number AS src, dst.account_number AS dst, r.amount AS amount, r.channel AS channel")
        for r in transfers:
            src, dst, amt, ch = str(r["src"]), str(r["dst"]), r["amount"], str(r["channel"])
            
            if "CYC" in src and "CYC" in dst:
                edge_color = "#ef4444" # Highlighted laundering cycle
                width = 3.5
            elif "KINGPIN" in dst:
                edge_color = "#f59e0b" # Funnel to Kingpin
                width = 2.5
            else:
                edge_color = "#334155"
                width = 1.0
                
            net.add_edge(src, dst, title=f"{ch}: ${amt:,}", label=f"${amt:,}", color=edge_color, width=width, font={"color": "#94a3b8", "size": 8})

    html_file = "temp_fincrime_graph.html"
    net.save_graph(html_file)
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
    return html

# ==========================================
# GEMINI AUTONOMOUS SAR GENERATOR
# ==========================================
def generate_regulatory_sar(typology_name, evidence_payload):
    client = get_gemini_client()
    if not client:
        return "⚠️ Add `GEMINI_API_KEY` to `.env` to unlock automated FinCEN-standard Suspicious Activity Report (SAR) generation."

    prompt = f"""
    You are a Principal AML Compliance Officer and Forensic Financial Crime Investigator.
    Generate a formal FinCEN-Standard Suspicious Activity Report (SAR) based strictly on the following Neo4j Knowledge Graph facts.

    --- FORENSIC EVIDENCE PAYLOAD ---
    Target Typology: {typology_name}
    Evidence Data: {json.dumps(evidence_payload, indent=2)}
    ---------------------------------

    Generate an Executive Suspicious Activity Report (SAR) structured as follows:
    1. **SECTION I: EXECUTIVE SUMMARY**: Summary of suspicious activity, total funds illicitly moved, and primary risk exposure.
    2. **SECTION II: INVOLVED PARTIES & IDENTIFIERS**: Table or list of involved account numbers, beneficial owners, and hardware/network identifiers.
    3. **SECTION III: SUSPICIOUS ACTIVITY NARRATIVE**: Step-by-step forensic breakdown of how the scheme operates (e.g. structuring, layering, round-tripping, or synthetic identity creation).
    4. **SECTION IV: RECOMMENDED ACTION & FREEZES**: Specific immediate actions (e.g., account debits freeze, SAR filing with regulatory authorities, law enforcement referral).
    """
    try:
        response = client.chats.create(model='gemini-3.5-flash-lite').send_message(prompt)
        return response.text
    except Exception as e:
        return f"Gemini Advisory Notice: {e}"

# ==========================================
# SIDEBAR ARCHITECTURE
# ==========================================
st.sidebar.markdown("## ⚙️ FraudShield Engine")
st.sidebar.markdown("""
- **Graph Engine:** Neo4j Aura Cloud GDS
- **Algorithms:** Cycles, Community Detection, Mule Centrality
- **AI Investigator:** Google Gemini Flash
- **Standard:** FinCEN / BSA / FATF Compliance
""")

st.sidebar.write("---")
st.sidebar.markdown("### 🔍 Forensic Typology Scanner")
selected_scanner = st.sidebar.radio(
    "Select Typology to Investigate:",
    ["🔄 Circular Laundering Rings", "📱 Synthetic Identity Device Farms", "🐟 Smurfing & Mule Aggregation"]
)

st.sidebar.write("---")
st.sidebar.markdown("[🌐 Sonny Honey Portfolio](https://adjacency.xyz)")
st.sidebar.markdown("[📄 GraphRAG Deep Dive](https://adjacency.xyz/articles/why-vector-search-fails-graphrag.html)")

# ==========================================
# MAIN INTERFACE
# ==========================================
st.markdown('<p class="main-title">🛡️ FraudShield-GraphAI Engine</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Enterprise Financial Crime, AML & Fraud Ring Intelligence Platform powered by Neo4j & Google Gemini</p>', unsafe_allow_html=True)

# Value Proposition Banner
st.markdown("""
<div style="background: #111726; border: 1px solid #1e293b; border-radius: 12px; padding: 18px 24px; margin-bottom: 25px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
        <div>
            <div style="color: #ef4444; font-weight: 700; font-size: 0.85rem; font-family: monospace;">ROUND-TRIPPING DETECTION</div>
            <p style="color: #FFFFFF; font-size: 1rem; font-weight: 700; margin: 4px 0 0 0;">Closed-Loop Circular Fund Laundering</p>
        </div>
        <div>
            <div style="color: #ef4444; font-weight: 700; font-size: 0.85rem; font-family: monospace;">SYNTHETIC IDENTITY PROOF</div>
            <p style="color: #FFFFFF; font-size: 1rem; font-weight: 700; margin: 4px 0 0 0;">Device-Farm &amp; Hardware Fingerprint Linkage</p>
        </div>
        <div>
            <div style="color: #ef4444; font-weight: 700; font-size: 0.85rem; font-family: monospace;">AUTONOMOUS COMPLIANCE</div>
            <p style="color: #FFFFFF; font-size: 1rem; font-weight: 700; margin: 4px 0 0 0;">Instant FinCEN-Standard SAR Generation</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# DYNAMIC TYPOLOGY DASHBOARD PANELS
# ==========================================

if selected_scanner == "🔄 Circular Laundering Rings":
    st.markdown("### 🔄 Circular Fund Laundering Ring Detection (Layering Cycles)")
    st.caption("Identifies closed-loop round-tripping transfers ($A \to B \to C \to D \to A$) designed to disguise criminal origins.")
    
    rings = scan_circular_rings()
    if rings:
        r = rings[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Identified Ring Cycle</div><div class="metric-value">{r["hop_count"]} Hops Closed-Loop</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Total Laundered Volume</div><div class="metric-value">${r["total_flow"]:,} USD</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Compliance Risk Level</div><div class="metric-value" style="color: #ef4444;">CRITICAL (FATF Red Flag)</div></div>', unsafe_allow_html=True)
            
        st.write("")
        st.markdown(f"**🚨 Detected Ring Sequence:** `{' ➔ '.join(r['cycle_accounts'])}`")
        evidence = r
    else:
        st.info("No active circular fund rings detected.")
        evidence = {}

elif selected_scanner == "📱 Synthetic Identity Device Farms":
    st.markdown("### 📱 Synthetic Identity & Device Farm Detection")
    st.caption("Uncovers multiple distinct accounts operating off shared emulator hardware IDs, root exploits, and VPN IPs.")
    
    farms = scan_synthetic_device_farms()
    if farms:
        f = farms[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Accounts on Single Device</div><div class="metric-value">{f["farm_size"]} Accounts Linked</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Target Device Identifier</div><div class="metric-value">{f["device_id"]}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Proxy IP Origin</div><div class="metric-value">{f["ip_address"]} ({f["ip_country"]})</div></div>', unsafe_allow_html=True)
            
        st.write("")
        st.markdown(f"**Linked Accounts:** `{', '.join(f['linked_accounts'])}`")
        st.markdown(f"**Beneficial Names Claimed:** `{', '.join(f['linked_customers'])}`")
        evidence = f
    else:
        st.info("No active device farms detected.")
        evidence = {}

else: # Smurfing & Mule Funnels
    st.markdown("### 🐟 Smurfing & Structured Mule Funnel Detection")
    st.caption("Detects structured deposits (sub-$10,000 threshold) aggregating into a single master account.")
    
    mules = scan_smurfing_mule_networks()
    if mules:
        m = mules[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Aggregated Kingpin Account</div><div class="metric-value">{m["kingpin_account"]}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Coordinated Money Mules</div><div class="metric-value">{m["mule_count"]} Mule Accounts</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-title">Total Funneled Proceeds</div><div class="metric-value">${m["total_funneled"]:,} USD</div></div>', unsafe_allow_html=True)
            
        st.write("")
        st.markdown(f"**Primary Beneficiary:** `{m['kingpin_name']}` (`{m['kingpin_account']}`)")
        with st.expander("🔍 View Structured Deposit Log (Below $10k Threshold)", expanded=True):
            st.dataframe(pd.DataFrame(m["deposits"]), use_container_width=True)
        evidence = m
    else:
        st.info("No active smurfing networks detected.")
        evidence = {}

st.write("---")

# ==========================================
# INTERACTIVE PYVIS FORENSIC GRAPH
# ==========================================
st.markdown("### 🕸️ Interactive Financial Network Forensics")
st.caption("Color Key: 🚨 **Red**: Circular Laundering Ring | 👑 **Amber**: Cash-Out Kingpin | 📱 **Purple**: Device Farm Accounts | 🐟 **Blue**: Money Mules | ✅ **Green**: Clean Retail")

graph_html = render_fincrime_subgraph()
components.html(graph_html, height=520, scrolling=False)

st.write("---")

# ==========================================
# AUTONOMOUS REGULATORY SAR GENERATION
# ==========================================
st.markdown("### 🤖 Autonomous Regulatory SAR Report (FinCEN Standard)")
st.caption("Generate an audit-proof Suspicious Activity Report backed by verifiable Neo4j topological proof.")

if st.button("🚨 Generate Formal Regulatory SAR with Gemini"):
    with st.spinner("Compiling Neo4j forensic evidence and generating formal FinCEN SAR dossier..."):
        sar_report = generate_regulatory_sar(selected_scanner, evidence)
        st.success("✅ Formal Suspicious Activity Report (SAR) Generated Successfully")
        st.markdown(sar_report)
        
        st.write("---")
        st.markdown("#### 📥 Export Regulatory Compliance Filing")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="📄 Download Official SAR (.md)",
                data=sar_report,
                file_name=f"FinCEN_SAR_{selected_scanner.replace(' ', '_')}.md",
                mime="text/markdown"
            )
        with d_col2:
            st.download_button(
                label="📊 Download Evidence Data (.json)",
                data=json.dumps(evidence, indent=2),
                file_name=f"Evidence_{selected_scanner.replace(' ', '_')}.json",
                mime="application/json"
            )

cleanup_temp_files()