import os
import sys
import random
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv(override=True)

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+ssc://51204372.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "51204372")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    print("❌ ERROR: NEO4J_PASSWORD is not set in environment variables.")
    sys.exit(1)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def init_schema():
    print("\n⚙️  Applying Database Constraints and Indexes for Financial Graph...")
    with driver.session() as session:
        session.run("CREATE CONSTRAINT customer_id_uniq IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE")
        session.run("CREATE CONSTRAINT account_no_uniq IF NOT EXISTS FOR (a:Account) REQUIRE a.account_number IS UNIQUE")
        session.run("CREATE CONSTRAINT device_id_uniq IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE")
        session.run("CREATE CONSTRAINT ip_addr_uniq IF NOT EXISTS FOR (ip:IPAddress) REQUIRE ip.ip IS UNIQUE")
        session.run("CREATE INDEX account_type_idx IF NOT EXISTS FOR (a:Account) ON (a.type)")
        print("✅ Constraints and performance indexes applied.")

def seed_financial_graph():
    print("\n📦 Generating Financial Crime Typologies & Banking Network...")

    # =========================================================================
    # 1. TYPOLOGY 1: CIRCULAR FUND TRANSFER RING (5-HOP ROUND-TRIPPING CYCLE)
    # =========================================================================
    print("  • Seeding Typology 1: Circular Fund Laundering Ring ($45k Loop)...")
    cycle_customers = [
        {"id": "CUST_CYC_01", "name": "Arthur Pendelton", "email": "a.pendelton@offshore-holdings.ch", "risk_rating": "HIGH"},
        {"id": "CUST_CYC_02", "name": "Balthazar Vance", "email": "bvance@panama-advisory.pa", "risk_rating": "HIGH"},
        {"id": "CUST_CYC_03", "name": "Cordelia Cross", "email": "ccross@cayman-trust.ky", "risk_rating": "HIGH"},
        {"id": "CUST_CYC_04", "name": "Dmitri Volkov", "email": "dvolkov@cyprus-capital.cy", "risk_rating": "HIGH"},
        {"id": "CUST_CYC_05", "name": "Evangeline Roux", "email": "eroux@lux-management.lu", "risk_rating": "HIGH"},
    ]
    cycle_accounts = [
        {"account_number": "ACC_CYC_01", "type": "Corporate Checking", "balance": 185000, "flag": "UNDER_INVESTIGATION", "cust_id": "CUST_CYC_01"},
        {"account_number": "ACC_CYC_02", "type": "Private Wealth", "balance": 92000, "flag": "UNDER_INVESTIGATION", "cust_id": "CUST_CYC_02"},
        {"account_number": "ACC_CYC_03", "type": "Shell LLC", "balance": 140000, "flag": "UNDER_INVESTIGATION", "cust_id": "CUST_CYC_03"},
        {"account_number": "ACC_CYC_04", "type": "Investment Custody", "balance": 78000, "flag": "UNDER_INVESTIGATION", "cust_id": "CUST_CYC_04"},
        {"account_number": "ACC_CYC_05", "type": "Trade Settlement", "balance": 115000, "flag": "UNDER_INVESTIGATION", "cust_id": "CUST_CYC_05"},
    ]
    cycle_transfers = [
        {"from": "ACC_CYC_01", "to": "ACC_CYC_02", "amount": 45000, "tx_id": "TX_CYC_101", "time": "2026-10-01T08:15:00Z", "channel": "WIRE"},
        {"from": "ACC_CYC_02", "to": "ACC_CYC_03", "amount": 44500, "tx_id": "TX_CYC_102", "time": "2026-10-01T09:30:00Z", "channel": "WIRE"},
        {"from": "ACC_CYC_03", "to": "ACC_CYC_04", "amount": 44000, "tx_id": "TX_CYC_103", "time": "2026-10-01T11:00:00Z", "channel": "WIRE"},
        {"from": "ACC_CYC_04", "to": "ACC_CYC_05", "amount": 43500, "tx_id": "TX_CYC_104", "time": "2026-10-01T13:45:00Z", "channel": "WIRE"},
        {"from": "ACC_CYC_05", "to": "ACC_CYC_01", "amount": 43000, "tx_id": "TX_CYC_105", "time": "2026-10-01T16:20:00Z", "channel": "WIRE"},
    ]

    # =========================================================================
    # 2. TYPOLOGY 2: SYNTHETIC IDENTITY & DEVICE FARM (SHARED HARDWARE & IP)
    # =========================================================================
    print("  • Seeding Typology 2: Synthetic Identity Device Farm (Shared IMEI & IP)...")
    shared_device = {"device_id": "DEV_FARM_999", "type": "Emulated Android", "os": "Android 14 Rooted", "imei": "358912059128311"}
    shared_ip = {"ip": "198.51.100.42", "country": "Seychelles", "is_vpn": True}
    
    farm_customers = [
        {"id": f"CUST_FARM_0{i}", "name": name, "email": f"user_{i}@tempmail-fast.xyz", "risk_rating": "MEDIUM"}
        for i, name in enumerate(["Liam Vance", "Noah Sterling", "Oliver Hayes", "Lucas Mercer", "Mason Drake", "Ethan Blackwood", "Aiden Frost"], 1)
    ]
    farm_accounts = [
        {"account_number": f"ACC_FARM_0{i}", "type": "Online Checking", "balance": random.randint(1200, 4500), "flag": "SUSPECT_SYNTHETIC", "cust_id": f"CUST_FARM_0{i}"}
        for i in range(1, 8)
    ]

    # =========================================================================
    # 3. TYPOLOGY 3: SMURFING / MULE FAN-IN AGGREGATION NETWORK
    # =========================================================================
    print("  • Seeding Typology 3: Smurfing Network (10 Mules Funneling into Kingpin)...")
    kingpin_cust = {"id": "CUST_KINGPIN_01", "name": "Victor 'The Broker' Sterling", "email": "v.sterling@apex-commodities.sg", "risk_rating": "CRITICAL"}
    kingpin_acc = {"account_number": "ACC_KINGPIN_01", "type": "Commercial Offshore", "balance": 480000, "flag": "PRIMARY_CASH_OUT", "cust_id": "CUST_KINGPIN_01"}

    mule_customers = []
    mule_accounts = []
    mule_transfers = []
    base_time = datetime(2026, 10, 2, 10, 0, 0)
    
    for i in range(1, 11):
        m_cust_id = f"CUST_MULE_{i:02d}"
        m_acc_no = f"ACC_MULE_{i:02d}"
        mule_customers.append({"id": m_cust_id, "name": f"Money Mule #{i:02d}", "email": f"mule_{i}@inbox-anon.org", "risk_rating": "HIGH"})
        mule_accounts.append({"account_number": m_acc_no, "type": "Retail Checking", "balance": 350, "flag": "MONEY_MULE", "cust_id": m_cust_id})
        
        # Structured deposit under $10,000 threshold ($9,400 to $9,800)
        structured_amount = random.randint(9400, 9850)
        tx_time = (base_time + timedelta(minutes=i*12)).strftime("%Y-%m-%dT%H:%M:%SZ")
        mule_transfers.append({
            "from": m_acc_no, "to": "ACC_KINGPIN_01", "amount": structured_amount,
            "tx_id": f"TX_MULE_{i:02d}", "time": tx_time, "channel": "INSTANT_ACH"
        })

    # =========================================================================
    # 4. LEGITIMATE BACKGROUND NOISE (STANDARD RETAIL BANKING)
    # =========================================================================
    print("  • Seeding Legitimate Retail Banking Background Activity...")
    legit_customers = [
        {"id": f"CUST_LEGIT_0{i}", "name": name, "email": f"{name.lower().replace(' ', '.')}@gmail.com", "risk_rating": "LOW"}
        for i, name in enumerate(["Sarah Jenkins", "Michael Chang", "Amara Okafor", "David Miller", "Elena Rostova", "Hiroshi Tanaka"], 1)
    ]
    legit_accounts = [
        {"account_number": f"ACC_LEGIT_0{i}", "type": "Personal Checking", "balance": random.randint(3000, 18000), "flag": "CLEAN", "cust_id": f"CUST_LEGIT_0{i}"}
        for i in range(1, 7)
    ]
    legit_transfers = [
        {"from": "ACC_LEGIT_01", "to": "ACC_LEGIT_02", "amount": 120, "tx_id": "TX_LEGIT_01", "time": "2026-10-03T12:00:00Z", "channel": "P2P"},
        {"from": "ACC_LEGIT_03", "to": "ACC_LEGIT_04", "amount": 450, "tx_id": "TX_LEGIT_02", "time": "2026-10-03T14:30:00Z", "channel": "P2P"},
        {"from": "ACC_LEGIT_05", "to": "ACC_LEGIT_06", "amount": 80, "tx_id": "TX_LEGIT_03", "time": "2026-10-03T18:15:00Z", "channel": "P2P"},
    ]

    with driver.session() as session:
        # Ingest Customers
        all_customers = cycle_customers + farm_customers + [kingpin_cust] + mule_customers + legit_customers
        session.run("""
        UNWIND $custs AS c
        MERGE (cust:Customer {id: c.id})
        SET cust.name = c.name, cust.email = c.email, cust.risk_rating = c.risk_rating
        """, custs=all_customers)

        # Ingest Accounts and link to Customers
        all_accounts = cycle_accounts + farm_accounts + [kingpin_acc] + mule_accounts + legit_accounts
        session.run("""
        UNWIND $accs AS a
        MERGE (acc:Account {account_number: a.account_number})
        SET acc.type = a.type, acc.balance = a.balance, acc.flag = a.flag
        WITH acc, a
        MATCH (c:Customer {id: a.cust_id})
        MERGE (c)-[:OWNS_ACCOUNT]->(acc)
        """, accs=all_accounts)

        # Ingest Device & IP for Farm
        session.run("""
        MERGE (d:Device {device_id: $dev.device_id})
        SET d.type = $dev.type, d.os = $dev.os, d.imei = $dev.imei
        MERGE (ip:IPAddress {ip: $ip.ip})
        SET ip.country = $ip.country, ip.is_vpn = $ip.is_vpn
        MERGE (d)-[:ROUTED_THROUGH]->(ip)
        WITH d
        UNWIND $acc_nos AS acc_no
        MATCH (acc:Account {account_number: acc_no})
        MERGE (acc)-[:LOGGED_IN_FROM {session_id: 'SESS_' + acc_no}]->(d)
        """, dev=shared_device, ip=shared_ip, acc_nos=[a["account_number"] for a in farm_accounts])

        # Ingest Transfers
        all_transfers = cycle_transfers + mule_transfers + legit_transfers
        session.run("""
        UNWIND $txs AS tx
        MATCH (src:Account {account_number: tx.from})
        MATCH (dst:Account {account_number: tx.to})
        MERGE (src)-[r:TRANSFERS_TO {transaction_id: tx.tx_id}]->(dst)
        SET r.amount = tx.amount, r.timestamp = tx.time, r.channel = tx.channel
        """, txs=all_transfers)

    print("✅ Financial Crime Knowledge Graph successfully ingested!")

def verify_fincrime_metrics():
    print("\n" + "="*60)
    print("📊 FRAUDSHIELD KNOWLEDGE GRAPH AUDIT METRICS")
    print("="*60)
    with driver.session() as session:
        n_cust = session.run("MATCH (c:Customer) RETURN count(c) AS count").single()['count']
        n_acc = session.run("MATCH (a:Account) RETURN count(a) AS count").single()['count']
        n_tx = session.run("MATCH ()-[r:TRANSFERS_TO]->() RETURN count(r) AS count").single()['count']
        n_farm = session.run("MATCH (a:Account)-[:LOGGED_IN_FROM]->(d:Device) RETURN count(a) AS count").single()['count']
        
        print(f"• Total Customer Identities: {n_cust}")
        print(f"• Total Bank Accounts:        {n_acc}")
        print(f"• Transaction Edges:          {n_tx}")
        print(f"• Device-Farm Bound Accounts: {n_farm}")
        
        print("\n🔍 Detecting Circular Money Laundering Ring (Cypher Path Match):")
        cycle_res = session.run("""
        MATCH path = (a:Account)-[:TRANSFERS_TO*3..6]->(a)
        RETURN [n IN nodes(path) | n.account_number] AS Ring, 
               reduce(tot = 0, r IN relationships(path) | tot + r.amount) AS TotalAmount
        LIMIT 1
        """)
        rec = cycle_res.single()
        if rec:
            print(f"  🚨 Detected Cycle: {' ➔ '.join(rec['Ring'])}")
            print(f"  💰 Laundered Flow: ${rec['TotalAmount']:,} USD")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        init_schema()
        seed_financial_graph()
        verify_fincrime_metrics()
        print("🎉 FraudShield Knowledge Graph is ready for GDS analysis!")
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
    finally:
        driver.close()