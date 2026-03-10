"""
☀️ AUTONOMOUS AI SOLAR MICROGRID MANAGEMENT SYSTEM
Single-file Streamlit app — zero import issues, deploy anywhere.

Run: streamlit run app.py
Upload ONLY: app.py + models/ folder + requirements.txt
"""

# ══════════════════════════════════════════════════════════════════════════════
#  IMPORTS
# ══════════════════════════════════════════════════════════════════════════════
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sqlite3, hashlib, os, math, random, joblib
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
DB_PATH   = "solar_microgrid.db"
MODEL_DIR = "models"

PRICE_PER_KWH = 0.18
FIXED_CHARGE  = 5.00
SOLAR_DISCOUNT= 0.10
OWM_BASE      = "https://api.openweathermap.org/data/2.5/weather"

GEN_COLS  = ["Solar_Irradiance","Cloud_Cover","Temperature","Humidity"]
DIST_COLS = ["Solar_Generation_kW","Battery_Level","Total_Load_kW",
             "Hospital_Load_kW","Residential_Load_kW","EV_Load_kW",
             "Emergency_Load_kW","Grid_Price"]

SECTOR_RATES = {"Hospital":0.12,"Emergency":0.10,"Residential":0.18,
                "EV_Charging":0.22,"Admin":0.15}

ACTION_COLORS = {"Hospital_Priority":"#FF3D5A","Emergency_Priority":"#FF6B00",
                 "Residential_Support":"#00D4FF","EV_Charging_Priority":"#00FF94",
                 "Balanced_Distribution":"#F5A623","EV_Charging_Allowed":"#00FF94"}
ACTION_ICONS  = {"Hospital_Priority":"🏥","Emergency_Priority":"🚨",
                 "Residential_Support":"🏘️","EV_Charging_Priority":"🔌",
                 "Balanced_Distribution":"⚖️","EV_Charging_Allowed":"🚗"}

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
:root{
  --gold:#F5A623;--amber:#FF6B00;--blue:#00D4FF;--navy:#050A1A;
  --panel:#0A1628;--card:#0F1F3D;--border:#1E3A5F;--text:#E8F4FD;
  --muted:#7BA3C4;--green:#00FF94;--red:#FF3D5A;
}
html,body,[data-testid="stAppViewContainer"]{
  background:var(--navy)!important;font-family:'Rajdhani',sans-serif;color:var(--text);
}
[data-testid="stSidebar"]{background:var(--panel)!important;}
.stButton>button{
  background:linear-gradient(135deg,var(--amber),var(--gold))!important;
  color:#000!important;font-family:'Orbitron',sans-serif!important;
  font-weight:700!important;border:none!important;border-radius:8px!important;
  transition:all 0.3s!important;
}
.stButton>button:hover{transform:translateY(-2px);box-shadow:0 8px 25px rgba(245,166,35,0.4)!important;}
.stTextInput>div>div>input,.stNumberInput>div>div>input{
  background:var(--card)!important;border:1px solid var(--border)!important;
  color:var(--text)!important;border-radius:8px!important;font-family:'Rajdhani',sans-serif!important;
}
.stSelectbox>div>div{background:var(--card)!important;border:1px solid var(--border)!important;}
h1,h2,h3{font-family:'Orbitron',sans-serif!important;color:var(--gold)!important;}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.5rem;}
.metric-card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.2rem 1.5rem;text-align:center;}
.mval{font-family:'Orbitron',sans-serif;font-size:2rem;font-weight:900;color:var(--gold);}
.mlabel{font-size:0.75rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-top:0.2rem;}
.section{font-family:'Orbitron',sans-serif;font-size:0.9rem;color:var(--blue);
  letter-spacing:2px;border-bottom:1px solid var(--border);padding-bottom:0.5rem;margin:1.5rem 0 1rem;}
.status-bar{background:var(--card);border:1px solid var(--border);border-radius:10px;
  padding:0.8rem 1.5rem;display:flex;gap:2rem;align-items:center;flex-wrap:wrap;margin-bottom:1rem;}
.pulse{display:inline-block;width:8px;height:8px;background:var(--green);
  border-radius:50%;animation:pulse 2s infinite;margin-right:5px;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
.ai-badge{display:inline-block;background:rgba(0,212,255,0.1);border:1px solid rgba(0,212,255,0.3);
  border-radius:50px;padding:0.3rem 1rem;font-size:0.8rem;color:var(--blue);letter-spacing:1px;}
.bill-line{display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid var(--border);}
.priority-card{background:var(--card);border-radius:14px;padding:1.2rem;text-align:center;border-left:4px solid;}
.login-title{font-family:'Orbitron',sans-serif;font-size:2.6rem;font-weight:900;
  background:linear-gradient(135deg,#F5A623,#FF6B00,#00D4FF);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px;}
.login-card{background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:2.5rem;max-width:420px;margin:1.5rem auto;box-shadow:0 20px 60px rgba(0,0,0,0.5);}
.demo-creds{background:rgba(0,212,255,0.05);border:1px solid rgba(0,212,255,0.2);
  border-radius:10px;padding:1rem 1.5rem;margin-top:1.5rem;font-size:0.88rem;color:var(--muted);}
.demo-creds strong{color:var(--blue);}
</style>
"""

# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE LAYER
# ══════════════════════════════════════════════════════════════════════════════
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            sector TEXT DEFAULT 'Residential');
        CREATE TABLE IF NOT EXISTS energy_usage(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            energy_consumed REAL NOT NULL,
            date TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            date TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS system_stats(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solar_generation REAL, battery_level REAL, total_load REAL,
            grid_price REAL, cloud_cover REAL, temperature REAL,
            humidity REAL, distribution_action TEXT, timestamp TEXT);
    """)
    for uname,pw,role,sector in [
        ("admin","admin123","admin","Admin"),
        ("hospital_user","pass123","user","Hospital"),
        ("resident1","pass123","user","Residential"),
        ("ev_user","pass123","user","EV_Charging"),
        ("emergency_user","pass123","user","Emergency"),
    ]:
        c.execute("SELECT id FROM users WHERE username=?",(uname,))
        if not c.fetchone():
            c.execute("INSERT INTO users(username,password,role,sector) VALUES(?,?,?,?)",
                      (uname,hash_pw(pw),role,sector))
    conn.commit(); conn.close()

def db_authenticate(username,password):
    conn=get_conn()
    row=conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                     (username,hash_pw(password))).fetchone()
    conn.close(); return dict(row) if row else None

def db_get_all_users():
    conn=get_conn()
    rows=conn.execute("SELECT id,username,role,sector FROM users").fetchall()
    conn.close(); return [dict(r) for r in rows]

def db_add_user(username,password,role="user",sector="Residential"):
    conn=get_conn()
    try:
        conn.execute("INSERT INTO users(username,password,role,sector) VALUES(?,?,?,?)",
                     (username,hash_pw(password),role,sector))
        conn.commit(); return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def db_delete_user(uid):
    conn=get_conn(); conn.execute("DELETE FROM users WHERE id=?",(uid,))
    conn.commit(); conn.close()

def db_log_energy(user_id,kwh):
    conn=get_conn()
    conn.execute("INSERT INTO energy_usage(user_id,energy_consumed,date) VALUES(?,?,?)",
                 (user_id,kwh,datetime.now().isoformat()))
    conn.commit(); conn.close()

def db_get_user_energy(user_id):
    conn=get_conn()
    rows=conn.execute("SELECT * FROM energy_usage WHERE user_id=? ORDER BY date DESC LIMIT 30",
                      (user_id,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def db_create_payment(user_id,amount):
    conn=get_conn()
    conn.execute("INSERT INTO payments(user_id,amount,status,date) VALUES(?,?,?,?)",
                 (user_id,amount,"paid",datetime.now().isoformat()))
    conn.commit(); conn.close()

def db_get_user_payments(user_id):
    conn=get_conn()
    rows=conn.execute("SELECT * FROM payments WHERE user_id=? ORDER BY date DESC",
                      (user_id,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def db_log_system_stats(d):
    conn=get_conn()
    conn.execute("""INSERT INTO system_stats
        (solar_generation,battery_level,total_load,grid_price,
         cloud_cover,temperature,humidity,distribution_action,timestamp)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (d.get("solar_generation"),d.get("battery_level"),d.get("total_load"),
         d.get("grid_price"),d.get("cloud_cover"),d.get("temperature"),
         d.get("humidity"),d.get("distribution_action"),datetime.now().isoformat()))
    conn.commit(); conn.close()

def db_get_system_stats(limit=200):
    conn=get_conn()
    rows=conn.execute("SELECT * FROM system_stats ORDER BY timestamp DESC LIMIT ?",(limit,)).fetchall()
    conn.close(); return [dict(r) for r in rows]

def db_get_latest_stat():
    conn=get_conn()
    row=conn.execute("SELECT * FROM system_stats ORDER BY timestamp DESC LIMIT 1").fetchone()
    conn.close(); return dict(row) if row else None

def db_get_all_energy_usage():
    conn=get_conn()
    rows=conn.execute("""SELECT u.username,u.sector,SUM(e.energy_consumed) as total
        FROM energy_usage e JOIN users u ON e.user_id=u.id
        GROUP BY u.id ORDER BY total DESC""").fetchall()
    conn.close(); return [dict(r) for r in rows]

# ══════════════════════════════════════════════════════════════════════════════
#  AI MODEL LAYER  (lazy-loaded, cached in session_state)
# ══════════════════════════════════════════════════════════════════════════════
def load_models():
    if "solar_model" not in st.session_state:
        try:
            st.session_state.solar_model = joblib.load(os.path.join(MODEL_DIR,"solar_prediction_model.pkl"))
            st.session_state.dist_model  = joblib.load(os.path.join(MODEL_DIR,"distribution_model.pkl"))
            st.session_state.dist_le     = joblib.load(os.path.join(MODEL_DIR,"distribution_label_encoder.pkl"))
            st.session_state.models_ok   = True
        except Exception as e:
            st.session_state.models_ok = False
            st.session_state.model_error = str(e)

def predict_solar(irr, cloud, temp, hum):
    load_models()
    if not st.session_state.get("models_ok"):
        return round(irr / 120 * (1 - cloud/100), 3)
    X = pd.DataFrame([[irr,cloud,temp,hum]], columns=GEN_COLS)
    return round(float(max(0.0, st.session_state.solar_model.predict(X)[0])), 3)

def predict_dist_action(solar,batt,total,hosp,res,ev,emg,price):
    load_models()
    if not st.session_state.get("models_ok"):
        return "Hospital_Priority"
    X = pd.DataFrame([[solar,batt,total,hosp,res,ev,emg,price]], columns=DIST_COLS)
    return st.session_state.dist_le.inverse_transform(st.session_state.dist_model.predict(X))[0]

def predict_dist_probs(solar,batt,total,hosp,res,ev,emg,price):
    load_models()
    if not st.session_state.get("models_ok"):
        return {"Hospital_Priority":0.97}
    X = pd.DataFrame([[solar,batt,total,hosp,res,ev,emg,price]], columns=DIST_COLS)
    probs = st.session_state.dist_model.predict_proba(X)[0]
    classes = st.session_state.dist_le.inverse_transform(range(len(probs)))
    return {c:round(float(p),4) for c,p in zip(classes,probs)}

# ══════════════════════════════════════════════════════════════════════════════
#  WEATHER ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def cloud_to_irradiance(cloud, temp, hour):
    hf = max(0, math.sin(math.pi*(hour-6)/12)) if 6<=hour<=18 else 0
    cf = 1-(cloud/100)*0.75
    tb = max(0,(temp-15)*2)
    return round(1000*hf*cf+tb, 2)

def fetch_weather(api_key="", city="London"):
    if api_key and api_key.strip() and REQUESTS_AVAILABLE:
        try:
            r = requests.get(OWM_BASE,
                params={"q":city,"appid":api_key,"units":"metric"}, timeout=5)
            if r.status_code == 200:
                d=r.json(); hour=datetime.now().hour
                cloud=d["clouds"]["all"]; temp=d["main"]["temp"]
                return {"temperature":temp,"humidity":d["main"]["humidity"],
                        "cloud_cover":cloud,"condition":d["weather"][0]["description"].title(),
                        "wind_speed":d["wind"]["speed"],
                        "solar_irradiance":cloud_to_irradiance(cloud,temp,hour),
                        "source":"live","city":city}
        except: pass
    hour=datetime.now().hour
    temp  = round(20+10*math.sin(math.pi*(hour-6)/12)+random.uniform(-2,2),1)
    cloud = round(random.uniform(10,70),1)
    hum   = round(random.uniform(40,85),1)
    return {"temperature":temp,"humidity":hum,"cloud_cover":cloud,
            "condition":random.choice(["Partly Cloudy","Sunny","Clear Sky","Overcast","Light Clouds"]),
            "wind_speed":round(random.uniform(2,15),1),
            "solar_irradiance":cloud_to_irradiance(cloud,temp,hour),
            "source":"simulated","city":city}

# ══════════════════════════════════════════════════════════════════════════════
#  ENERGY SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════
def simulate_loads(hour=None):
    if hour is None: hour=datetime.now().hour
    rf = 0.6+0.4*abs(math.sin(math.pi*(hour-7)/12))
    hf = 0.85+0.15*random.random()
    ef = 0.2+0.8*(1 if 18<=hour<=23 else 0.15)
    xf = 0.7+0.3*random.random()
    h=round(random.uniform(20,45)*hf,2); r=round(random.uniform(30,80)*rf,2)
    e=round(random.uniform(5,25)*ef,2);  x=round(random.uniform(8,20)*xf,2)
    return {"hospital_load":h,"residential_load":r,"ev_load":e,"emergency_load":x,"total_load":round(h+r+e+x,2)}

def update_battery(level, solar, load):
    net=(solar-load); delta=(net/500)*100
    new=max(5.0,min(100.0,level+delta+random.uniform(-0.5,0.5)))
    return {"battery_level":round(new,2),"charging":net>0,"net_power":round(net,2)}

def grid_price(hour=None):
    if hour is None: hour=datetime.now().hour
    if 7<=hour<=9 or 17<=hour<=21: return round(random.uniform(0.22,0.35),4)
    if hour>=22 or hour<=5:        return round(random.uniform(0.06,0.10),4)
    return round(random.uniform(0.12,0.20),4)

def microgrid_snapshot(weather, batt_level, solar_kw):
    hour=datetime.now().hour; loads=simulate_loads(hour)
    batt=update_battery(batt_level,solar_kw,loads["total_load"])
    price=grid_price(hour)
    eff=round(min(100,(solar_kw/max(loads["total_load"],1))*100),1)
    gi=max(0.0,round(loads["total_load"]-solar_kw-(batt_level-batt["battery_level"])*5,2))
    return {**loads,**batt,"solar_generation":solar_kw,"grid_price":price,
            "grid_import":gi,"efficiency":eff,"hour":hour,"timestamp":datetime.now().isoformat()}

# ══════════════════════════════════════════════════════════════════════════════
#  BILLING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def calculate_bill(kwh, solar_fraction=0.0):
    gross=round(kwh*PRICE_PER_KWH,2)
    disc =round(gross*SOLAR_DISCOUNT,2) if solar_fraction>=0.5 else 0.0
    return {"energy_consumed":kwh,"unit_rate":PRICE_PER_KWH,"gross_charge":gross,
            "fixed_charge":FIXED_CHARGE,"solar_discount":disc,
            "total_due":max(0.0,round(gross+FIXED_CHARGE-disc,2))}

# ══════════════════════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def batt_color(b): return "#00FF94" if b>40 else ("#F5A623" if b>20 else "#FF3D5A")

def sidebar_nav(user):
    with st.sidebar:
        st.markdown("<div style='font-family:Orbitron;font-size:1.1rem;color:#F5A623;padding:1rem 0'>☀️ SOLAR AI</div>",
                    unsafe_allow_html=True)
        st.markdown(f"**{user['username']}** | {user['role'].upper()}")
        st.markdown("---")
        pages = [("🏠 Dashboard","dashboard"),("👤 My Account","user"),
                 ("⚡ Distribution","distribution"),("🌤 Weather","weather"),
                 ("💳 Billing","billing")]
        if user["role"]=="admin": pages.append(("⚙️ Admin Panel","admin"))
        for label,page in pages:
            if st.button(label, use_container_width=True):
                st.session_state.page=page; st.rerun()
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["user","logged_in","page","battery_level"]:
                st.session_state.pop(k,None)
            st.rerun()
        api_key=st.text_input("🔑 OWM API Key",type="password",key="owm_key")
        city=st.text_input("📍 City",value="London",key="city_input")
        st.checkbox("🔄 Auto-refresh 30s",key="auto_refresh")
    return api_key, city

def dark_chart_layout(fig, height=300, **kw):
    fig.update_layout(template="plotly_dark",height=height,
        paper_bgcolor="#0F1F3D",plot_bgcolor="#0A1628",
        xaxis=dict(gridcolor="#1E3A5F"),yaxis=dict(gridcolor="#1E3A5F"),
        font=dict(family="Rajdhani"),margin=dict(t=20,b=40,l=40,r=10),**kw)
    return fig

def kpi_card(col, icon, value, label, color="#F5A623"):
    col.markdown(f"""
    <div class='metric-card'>
        <div style='font-size:1.8rem'>{icon}</div>
        <div class='mval' style='color:{color}'>{value}</div>
        <div class='mlabel'>{label}</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def page_login():
    st.markdown("""
    <div style='text-align:center;padding:2.5rem 0 1rem'>
        <div style='font-size:3.5rem'>☀️</div>
        <div class='login-title'>SOLAR MICROGRID AI</div>
        <div style='font-size:1rem;color:#7BA3C4;letter-spacing:3px;text-transform:uppercase;margin-top:0.5rem'>
            Autonomous Smart Energy Management
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='display:flex;gap:1rem;justify-content:center;margin:1.5rem 0;flex-wrap:wrap'>
        <div style='background:#0F1F3D;border:1px solid #1E3A5F;border-radius:50px;padding:0.4rem 1.1rem;font-size:0.82rem;color:#7BA3C4'>
            <span style='display:inline-block;width:8px;height:8px;background:#00FF94;border-radius:50%;margin-right:5px;animation:pulse 2s infinite'></span>
            System <span style='color:#F5A623'>ONLINE</span></div>
        <div style='background:#0F1F3D;border:1px solid #1E3A5F;border-radius:50px;padding:0.4rem 1.1rem;font-size:0.82rem;color:#7BA3C4'>
            AI Models <span style='color:#F5A623'>ACTIVE</span></div>
        <div style='background:#0F1F3D;border:1px solid #1E3A5F;border-radius:50px;padding:0.4rem 1.1rem;font-size:0.82rem;color:#7BA3C4'>
            Grid Nodes <span style='color:#F5A623'>247</span></div>
        <div style='background:#0F1F3D;border:1px solid #1E3A5F;border-radius:50px;padding:0.4rem 1.1rem;font-size:0.82rem;color:#7BA3C4'>
            Solar Panels <span style='color:#F5A623'>1,840</span></div>
    </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1,1.2,1])
    with mid:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-family:Orbitron;color:#F5A623;font-size:0.95rem;letter-spacing:2px;margin-bottom:1.2rem'>🔐 SECURE LOGIN</h3>",
                    unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter username", key="login_user")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pw")
        if st.button("⚡  ACCESS SYSTEM", use_container_width=True):
            if username and password:
                user = db_authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials.")
            else:
                st.warning("⚠️ Enter both fields.")
        st.markdown("""
        <div class='demo-creds'>
            <strong>Demo Credentials</strong><br><br>
            👑 Admin:&nbsp; <code>admin</code> / <code>admin123</code><br>
            🏥 Hospital:&nbsp; <code>hospital_user</code> / <code>pass123</code><br>
            🏘️ Resident:&nbsp; <code>resident1</code> / <code>pass123</code><br>
            🚗 EV User:&nbsp; <code>ev_user</code> / <code>pass123</code>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""<div style='text-align:center;margin-top:3rem;color:#1E3A5F;font-size:0.78rem;letter-spacing:1px'>
        SOLAR MICROGRID AI v2.0 &nbsp;•&nbsp; Random Forest ML &nbsp;•&nbsp; Real-Time Optimization
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_dashboard(user, api_key, city):
    if st.session_state.get("auto_refresh"):
        st.markdown('<meta http-equiv="refresh" content="30">', unsafe_allow_html=True)

    w  = fetch_weather(api_key, city)
    sk = predict_solar(w["solar_irradiance"],w["cloud_cover"],w["temperature"],w["humidity"])
    if "battery_level" not in st.session_state: st.session_state.battery_level=65.0
    snap = microgrid_snapshot(w, st.session_state.battery_level, sk)
    st.session_state.battery_level = snap["battery_level"]

    action = predict_dist_action(sk,snap["battery_level"],snap["total_load"],
        snap["hospital_load"],snap["residential_load"],snap["ev_load"],snap["emergency_load"],snap["grid_price"])
    db_log_system_stats({"solar_generation":sk,"battery_level":snap["battery_level"],
        "total_load":snap["total_load"],"grid_price":snap["grid_price"],
        "cloud_cover":w["cloud_cover"],"temperature":w["temperature"],
        "humidity":w["humidity"],"distribution_action":action})

    bc = batt_color(snap["battery_level"])
    ac = ACTION_COLORS.get(action,"#F5A623")
    ai_icon = ACTION_ICONS.get(action,"⚡")

    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem'>
        <div>
            <span style='font-family:Orbitron;font-size:1.8rem;color:#F5A623;font-weight:900'>⚡ MICROGRID CONTROL</span>
            <span class='ai-badge' style='margin-left:1rem'>AI ACTIVE</span>
        </div>
        <div style='color:#7BA3C4;font-size:0.88rem'>{datetime.now().strftime("%Y-%m-%d  %H:%M:%S")}</div>
    </div>
    <div class='status-bar'>
        <div><span class='pulse'></span>SYSTEM ONLINE</div>
        <div>🤖 AI: <strong style='color:#00D4FF'>{action.replace("_"," ")}</strong></div>
        <div>☀️ <strong style='color:#F5A623'>{w["condition"]}</strong> ({w.get("city",city)})</div>
        <div>🔋 <strong style='color:{bc}'>{snap["battery_level"]:.1f}%</strong></div>
        <div>📡 {'🌍 Live' if w["source"]=="live" else "🔄 Simulated"}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section'>REAL-TIME METRICS</div>", unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi_card(c1,"☀️",f"{sk:.2f} kW","Solar Generation","#F5A623")
    kpi_card(c2,"🔋",f"{snap['battery_level']:.1f}%","Battery Level",bc)
    kpi_card(c3,"⚡",f"{snap['total_load']:.1f} kW","Total Load","#00D4FF")
    kpi_card(c4,"🌡️",f"{w['temperature']:.1f}°C","Temperature","#FF6B00")
    kpi_card(c5,"☁️",f"{w['cloud_cover']:.1f}%","Cloud Cover","#7BA3C4")

    st.markdown("<div class='section'>ENERGY ANALYTICS</div>", unsafe_allow_html=True)
    stats = db_get_system_stats(60)
    ca, cb = st.columns([2,1])

    with ca:
        if stats:
            df=pd.DataFrame(stats[::-1]); df["timestamp"]=pd.to_datetime(df["timestamp"])
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=df["timestamp"],y=df["solar_generation"],
                name="Solar Gen (kW)",line=dict(color="#F5A623",width=2.5),
                fill="tozeroy",fillcolor="rgba(245,166,35,0.1)"))
            fig.add_trace(go.Scatter(x=df["timestamp"],y=df["total_load"],
                name="Total Load (kW)",line=dict(color="#00D4FF",width=2,dash="dot")))
            dark_chart_layout(fig,300,legend=dict(orientation="h",y=-0.25))
            st.plotly_chart(fig,use_container_width=True)
        else: st.info("Collecting data… refresh in a moment.")

    with cb:
        fig_g=go.Figure(go.Indicator(mode="gauge+number+delta",value=snap["battery_level"],
            title={"text":"Battery %","font":{"color":"#7BA3C4","family":"Orbitron","size":12}},
            delta={"reference":50,"increasing":{"color":"#00FF94"},"decreasing":{"color":"#FF3D5A"}},
            gauge={"axis":{"range":[0,100]},"bar":{"color":bc},"bgcolor":"#0A1628","borderwidth":0,
                   "steps":[{"range":[0,20],"color":"rgba(255,61,90,0.2)"},
                             {"range":[20,50],"color":"rgba(245,166,35,0.15)"},
                             {"range":[50,100],"color":"rgba(0,255,148,0.1)"}],
                   "threshold":{"line":{"color":"#00D4FF","width":3},"value":80}},
            number={"suffix":"%","font":{"color":bc,"family":"Orbitron"}}))
        fig_g.update_layout(height=280,paper_bgcolor="#0F1F3D",font_color="#E8F4FD",
                            margin=dict(t=40,b=20,l=20,r=20))
        st.plotly_chart(fig_g,use_container_width=True)

    cc,cd = st.columns(2)
    with cc:
        fig_p=go.Figure(go.Pie(
            labels=["Hospital","Residential","EV Charging","Emergency"],
            values=[snap["hospital_load"],snap["residential_load"],snap["ev_load"],snap["emergency_load"]],
            hole=0.55,marker=dict(colors=["#FF3D5A","#F5A623","#00D4FF","#00FF94"],
                                  line=dict(color="#050A1A",width=2)),
            textfont=dict(family="Rajdhani",size=13)))
        fig_p.add_annotation(text=f"{snap['total_load']:.1f} kW",showarrow=False,
            font=dict(size=15,color="#F5A623",family="Orbitron"),y=0.5)
        fig_p.update_layout(title=dict(text="Load Distribution",font=dict(color="#7BA3C4",family="Orbitron",size=11)),
            height=300,paper_bgcolor="#0F1F3D",font_color="#E8F4FD",
            margin=dict(t=40,b=10,l=10,r=10),legend=dict(orientation="h",y=-0.1))
        st.plotly_chart(fig_p,use_container_width=True)

    with cd:
        if stats and len(stats)>2:
            df2=pd.DataFrame(stats[::-1]); df2["timestamp"]=pd.to_datetime(df2["timestamp"])
            fig_b=go.Figure(go.Scatter(x=df2["timestamp"],y=df2["battery_level"],
                mode="lines",line=dict(color=bc,width=2.5),
                fill="tozeroy",fillcolor="rgba(0,255,148,0.08)"))
            dark_chart_layout(fig_b,300,yaxis=dict(gridcolor="#1E3A5F",range=[0,100]))
            fig_b.update_layout(title=dict(text="Battery History",font=dict(color="#7BA3C4",family="Orbitron",size=11)))
            st.plotly_chart(fig_b,use_container_width=True)

    st.markdown("<div class='section'>AI OPTIMIZATION DECISIONS</div>", unsafe_allow_html=True)
    d1,d2,d3 = st.columns(3)
    with d1:
        st.markdown(f"""<div class='metric-card' style='border-color:{ac}'>
            <div style='font-size:2.5rem'>{ai_icon}</div>
            <div style='font-family:Orbitron;font-size:1.05rem;color:{ac};margin-top:0.4rem'>{action.replace("_"," ")}</div>
            <div class='mlabel'>AI DISTRIBUTION DECISION</div>
        </div>""", unsafe_allow_html=True)
    with d2:
        eff=snap["efficiency"]; ec="#00FF94" if eff>70 else ("#F5A623" if eff>40 else "#FF3D5A")
        st.markdown(f"""<div class='metric-card'>
            <div class='mval' style='color:{ec}'>{eff:.1f}%</div>
            <div class='mlabel'>Solar Efficiency</div>
            <div style='margin-top:0.8rem;background:#1E3A5F;border-radius:8px;height:8px'>
                <div style='background:{ec};width:{min(eff,100):.0f}%;height:8px;border-radius:8px'></div>
            </div>
        </div>""", unsafe_allow_html=True)
    with d3:
        gc="#00FF94" if snap["grid_import"]==0 else "#F5A623"
        st.markdown(f"""<div class='metric-card'>
            <div class='mval' style='color:{gc}'>{snap["grid_import"]:.1f} kW</div>
            <div class='mlabel'>Grid Import</div>
            <div style='color:#7BA3C4;font-size:0.85rem;margin-top:0.4rem'>
                Price: ${snap["grid_price"]:.3f}/kWh</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: USER DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_user(user):
    uid=user["id"]; sector=user.get("sector","Residential")
    rate=SECTOR_RATES.get(sector,PRICE_PER_KWH)
    st.markdown(f"<h2>👤 {user['username'].upper()}'S ENERGY DASHBOARD</h2>",unsafe_allow_html=True)
    st.markdown(f"<p style='color:#7BA3C4'>Sector: <strong style='color:#F5A623'>{sector}</strong> | Rate: ${rate:.2f}/kWh</p>",unsafe_allow_html=True)

    rows=db_get_user_energy(uid)
    if len(rows)<5:
        for _ in range(10): db_log_energy(uid,round(random.uniform(5,30),2))
        rows=db_get_user_energy(uid)

    total=sum(r["energy_consumed"] for r in rows)
    bill=calculate_bill(total,solar_fraction=0.55)
    sys=db_get_latest_stat()

    st.markdown("<div class='section'>ACCOUNT OVERVIEW</div>",unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    kpi_card(c1,"⚡",f"{total:.1f} kWh","Total Consumed","#F5A623")
    kpi_card(c2,"💰",f"${bill['total_due']:.2f}","Amount Due","#FF3D5A")
    bc_=batt_color(sys["battery_level"]) if sys else "#7BA3C4"
    kpi_card(c3,"🔋",f"{sys['battery_level']:.1f}%" if sys else "—","Grid Battery",bc_)
    kpi_card(c4,"☀️",f"{sys['solar_generation']:.2f} kW" if sys else "—","Solar Now","#00D4FF")

    st.markdown("<div class='section'>ENERGY CONSUMPTION HISTORY</div>",unsafe_allow_html=True)
    df=pd.DataFrame(rows[::-1]); df["date"]=pd.to_datetime(df["date"])
    df["day"]=df["date"].dt.strftime("%m-%d %H:%M")
    fig=go.Figure(go.Bar(x=df["day"],y=df["energy_consumed"],
        marker_color="#F5A623",marker_line_color="#FF6B00",marker_line_width=1,
        text=df["energy_consumed"].round(1),textposition="outside",
        textfont=dict(color="#E8F4FD",size=10)))
    dark_chart_layout(fig,280,yaxis=dict(gridcolor="#1E3A5F",title="kWh"))
    st.plotly_chart(fig,use_container_width=True)

    st.markdown("<div class='section'>BILL BREAKDOWN</div>",unsafe_allow_html=True)
    b1,b2=st.columns(2)
    with b1:
        for k,v in [("Energy Consumed",f"{bill['energy_consumed']:.2f} kWh"),
                    ("Unit Rate",f"${bill['unit_rate']:.4f}/kWh"),
                    ("Gross Charge",f"${bill['gross_charge']:.2f}"),
                    ("Fixed Charge",f"${bill['fixed_charge']:.2f}"),
                    ("Solar Discount",f"-${bill['solar_discount']:.2f}")]:
            st.markdown(f"<div class='bill-line'><span style='color:#7BA3C4'>{k}</span><strong>{v}</strong></div>",
                        unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"<span style='font-family:Orbitron;font-size:1.3rem;color:#F5A623'>TOTAL DUE: ${bill['total_due']:.2f}</span>",
                    unsafe_allow_html=True)
    with b2:
        fig2=go.Figure(go.Pie(
            labels=["Gross","Fixed","Solar Discount"],
            values=[bill["gross_charge"],bill["fixed_charge"],bill["solar_discount"]],
            hole=0.5,marker=dict(colors=["#FF6B00","#00D4FF","#00FF94"],
                                  line=dict(color="#050A1A",width=2)),
            textfont=dict(family="Rajdhani")))
        fig2.update_layout(height=260,paper_bgcolor="#0F1F3D",font_color="#E8F4FD",
                           margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig2,use_container_width=True)

    if sys:
        st.markdown("<div class='section'>LIVE GRID STATUS</div>",unsafe_allow_html=True)
        bc2=batt_color(sys["battery_level"])
        st.markdown(f"""<div class='card'>
            <div style='display:flex;gap:3rem;flex-wrap:wrap'>
                <div><div class='mlabel'>Solar Generation</div>
                    <div class='mval' style='font-size:1.4rem;color:#F5A623'>{sys["solar_generation"]:.2f} kW</div></div>
                <div><div class='mlabel'>Battery Level</div>
                    <div class='mval' style='font-size:1.4rem;color:{bc2}'>{sys["battery_level"]:.1f}%</div></div>
                <div><div class='mlabel'>Grid Load</div>
                    <div class='mval' style='font-size:1.4rem;color:#00D4FF'>{sys["total_load"]:.1f} kW</div></div>
                <div><div class='mlabel'>AI Decision</div>
                    <div style='font-family:Orbitron;font-size:0.9rem;color:#00D4FF;margin-top:0.4rem'>{sys["distribution_action"]}</div></div>
            </div></div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def page_admin(user):
    if user["role"]!="admin":
        st.error("⛔ Admin access required."); return

    st.markdown("<h2>⚙️ SYSTEM ADMINISTRATION</h2>",unsafe_allow_html=True)
    stat=db_get_latest_stat(); stats=db_get_system_stats(100)
    all_users=db_get_all_users(); usage=db_get_all_energy_usage()

    st.markdown("<div class='section'>SYSTEM OVERVIEW</div>",unsafe_allow_html=True)
    c1,c2,c3,c4,c5=st.columns(5)
    kpi_card(c1,"👥",str(len(all_users)),"Total Users","#F5A623")
    kpi_card(c2,"☀️",f"{stat['solar_generation']:.2f} kW" if stat else "—","Solar Now","#00D4FF")
    kpi_card(c3,"⚡",f"{stat['total_load']:.1f} kW" if stat else "—","Grid Load","#FF6B00")
    kpi_card(c4,"🔋",f"{stat['battery_level']:.1f}%" if stat else "—","Battery","#00FF94")
    kpi_card(c5,"📊",f"{sum(r['total'] for r in usage):.1f} kWh" if usage else "—","Total Consumed","#7BA3C4")

    st.markdown("<div class='section'>USER MANAGEMENT</div>",unsafe_allow_html=True)
    tab1,tab2=st.tabs(["👥 All Users","➕ Add User"])
    with tab1:
        df_u=pd.DataFrame(all_users)
        st.dataframe(df_u,use_container_width=True,hide_index=True)
        st.markdown("<strong style='color:#FF3D5A'>⚠️ Delete User</strong>",unsafe_allow_html=True)
        opts={f"{u['username']} (ID:{u['id']})":u["id"] for u in all_users if u["role"]!="admin"}
        if opts:
            sel=st.selectbox("Select user to delete",list(opts.keys()))
            if st.button("🗑️ Delete User"):
                db_delete_user(opts[sel]); st.success("Deleted."); st.rerun()
    with tab2:
        with st.form("add_user"):
            nu=st.text_input("Username"); np_=st.text_input("Password",type="password")
            nr=st.selectbox("Role",["user","admin"])
            ns=st.selectbox("Sector",["Residential","Hospital","Emergency","EV_Charging"])
            if st.form_submit_button("➕ Add User"):
                if nu and np_:
                    ok=db_add_user(nu,np_,nr,ns)
                    st.success(f"✅ '{nu}' created.") if ok else st.error("Username taken.")
                else: st.warning("Fill all fields.")

    if usage:
        st.markdown("<div class='section'>TOP ENERGY CONSUMERS</div>",unsafe_allow_html=True)
        df_use=pd.DataFrame(usage).sort_values("total",ascending=False)
        ct,cc2=st.columns(2)
        with ct: st.dataframe(df_use,use_container_width=True,hide_index=True)
        with cc2:
            fig=go.Figure(go.Bar(x=df_use["username"],y=df_use["total"],
                marker=dict(color=df_use["total"],colorscale=[[0,"#0A1628"],[0.5,"#F5A623"],[1,"#FF6B00"]]),
                text=df_use["total"].round(1),textposition="outside"))
            dark_chart_layout(fig,300,yaxis=dict(gridcolor="#1E3A5F",title="kWh"))
            st.plotly_chart(fig,use_container_width=True)

    if stats:
        st.markdown("<div class='section'>SYSTEM STATISTICS</div>",unsafe_allow_html=True)
        df_s=pd.DataFrame(stats[::-1]); df_s["timestamp"]=pd.to_datetime(df_s["timestamp"])
        fig2=go.Figure()
        fig2.add_trace(go.Scatter(x=df_s["timestamp"],y=df_s["solar_generation"],
            name="Solar (kW)",line=dict(color="#F5A623",width=2)))
        fig2.add_trace(go.Scatter(x=df_s["timestamp"],y=df_s["total_load"],
            name="Load (kW)",line=dict(color="#00D4FF",width=2,dash="dot")))
        fig2.add_trace(go.Scatter(x=df_s["timestamp"],y=df_s["battery_level"],
            name="Battery %",line=dict(color="#00FF94",width=2),yaxis="y2"))
        dark_chart_layout(fig2,350,legend=dict(orientation="h",y=-0.2),
            yaxis2=dict(overlaying="y",side="right",showgrid=False,range=[0,100]))
        st.plotly_chart(fig2,use_container_width=True)

        ac_cnt=df_s["distribution_action"].value_counts().reset_index()
        ac_cnt.columns=["action","count"]
        fig3=go.Figure(go.Pie(labels=ac_cnt["action"],values=ac_cnt["count"],hole=0.5,
            marker=dict(colors=["#FF3D5A","#F5A623","#00D4FF","#00FF94"],
                        line=dict(color="#050A1A",width=2)),
            textfont=dict(family="Rajdhani")))
        fig3.update_layout(
            title=dict(text="Distribution Action Frequency",font=dict(color="#7BA3C4",family="Orbitron",size=11)),
            height=300,paper_bgcolor="#0F1F3D",font_color="#E8F4FD",margin=dict(t=40,b=10,l=10,r=10))
        st.plotly_chart(fig3,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: ENERGY DISTRIBUTION
# ══════════════════════════════════════════════════════════════════════════════
def page_distribution(user, api_key, city):
    st.markdown("<h2>⚡ AI ENERGY DISTRIBUTION</h2>",unsafe_allow_html=True)
    st.markdown("<p style='color:#7BA3C4'>Autonomous power allocation across all sectors in real time</p>",unsafe_allow_html=True)

    w=fetch_weather(api_key,city)
    sk=predict_solar(w["solar_irradiance"],w["cloud_cover"],w["temperature"],w["humidity"])
    if "battery_level" not in st.session_state: st.session_state.battery_level=65.0
    snap=microgrid_snapshot(w,st.session_state.battery_level,sk)
    st.session_state.battery_level=snap["battery_level"]

    action=predict_dist_action(sk,snap["battery_level"],snap["total_load"],
        snap["hospital_load"],snap["residential_load"],snap["ev_load"],snap["emergency_load"],snap["grid_price"])
    probs=predict_dist_probs(sk,snap["battery_level"],snap["total_load"],
        snap["hospital_load"],snap["residential_load"],snap["ev_load"],snap["emergency_load"],snap["grid_price"])

    # Sankey diagram
    st.markdown("<div class='section'>ENERGY FLOW DIAGRAM</div>",unsafe_allow_html=True)
    h_from_s=min(sk*0.35,snap["hospital_load"])
    r_from_s=min(sk*0.40,snap["residential_load"])
    e_from_s=min(sk*0.15,snap["ev_load"])
    x_from_s=min(sk*0.10,snap["emergency_load"])
    gi=max(0,snap["grid_import"])

    link_src=[0,0,0,0]; link_tgt=[3,4,5,6]
    link_val=[max(0.01,h_from_s),max(0.01,r_from_s),max(0.01,e_from_s),max(0.01,x_from_s)]
    link_clr=["rgba(255,61,90,0.5)","rgba(0,212,255,0.5)","rgba(0,212,255,0.3)","rgba(255,107,0,0.5)"]

    if snap["battery_level"]>20 and snap["net_power"]<0:
        link_src+=[1]; link_tgt+=[3]; link_val+=[max(0.01,snap["hospital_load"]*0.2)]
        link_clr+=["rgba(0,255,148,0.4)"]
    if gi>0:
        link_src+=[2]; link_tgt+=[4]; link_val+=[max(0.01,gi)]; link_clr+=["rgba(0,212,255,0.3)"]

    fig_s=go.Figure(go.Sankey(
        node=dict(pad=20,thickness=25,
            label=["☀️ Solar","🔋 Battery","🔌 Grid Import","🏥 Hospital","🏘️ Residential","🚗 EV Charging","🚨 Emergency"],
            color=["#F5A623","#00FF94","#00D4FF","#FF3D5A","#7BA3C4","#00D4FF","#FF6B00"],
            line=dict(color="#050A1A",width=1)),
        link=dict(source=link_src,target=link_tgt,value=link_val,color=link_clr)))
    fig_s.update_layout(height=380,paper_bgcolor="#0F1F3D",
        font=dict(family="Rajdhani",size=14,color="#E8F4FD"),margin=dict(t=20,b=20,l=20,r=20))
    st.plotly_chart(fig_s,use_container_width=True)

    # Priority cards
    st.markdown("<div class='section'>SECTOR ALLOCATION (AI PRIORITY ORDER)</div>",unsafe_allow_html=True)
    sectors=[("🏥 Hospital",snap["hospital_load"],"#FF3D5A",1,"Critical"),
             ("🚨 Emergency",snap["emergency_load"],"#FF6B00",2,"High Urgency"),
             ("🏘️ Residential",snap["residential_load"],"#00D4FF",3,"Standard"),
             ("🚗 EV Charging",snap["ev_load"],"#00FF94",4,"Flexible")]
    cols=st.columns(4)
    for col,(label,load,color,prio,note) in zip(cols,sectors):
        pct=round((load/max(snap["total_load"],1))*100,1)
        with col:
            st.markdown(f"""<div class='priority-card' style='border-left-color:{color}'>
                <div style='font-size:1.6rem'>{label.split()[0]}</div>
                <div style='font-family:Orbitron;color:{color};font-size:1.3rem;margin:0.4rem 0'>{load:.1f} kW</div>
                <div style='color:#7BA3C4;font-size:0.8rem'>PRIORITY #{prio}</div>
                <div style='margin:0.6rem 0;background:#1E3A5F;border-radius:6px;height:6px'>
                    <div style='background:{color};width:{min(pct,100):.0f}%;height:6px;border-radius:6px'></div>
                </div>
                <div style='font-size:0.75rem;color:#7BA3C4'>{pct}% | {note}</div>
            </div>""",unsafe_allow_html=True)

    # AI confidence
    st.markdown("<div class='section'>AI DECISION CONFIDENCE</div>",unsafe_allow_html=True)
    sorted_p=sorted(probs.items(),key=lambda x:-x[1])
    cp,ca2=st.columns(2)
    with cp:
        p_labels=[k.replace("_"," ") for k,_ in sorted_p]
        p_vals=[v*100 for _,v in sorted_p]
        p_colors=["#F5A623" if k==action else "#1E3A5F" for k,_ in sorted_p]
        fig_pb=go.Figure(go.Bar(x=p_vals,y=p_labels,orientation="h",
            marker_color=p_colors,text=[f"{v:.1f}%" for v in p_vals],
            textposition="inside",textfont=dict(color="#E8F4FD",family="Rajdhani")))
        dark_chart_layout(fig_pb,250,xaxis=dict(range=[0,100],gridcolor="#1E3A5F",title="Confidence %"))
        st.plotly_chart(fig_pb,use_container_width=True)
    with ca2:
        top_a,top_p=sorted_p[0]; ac=ACTION_COLORS.get(top_a,"#F5A623")
        st.markdown(f"""<div class='card' style='text-align:center;border-color:{ac}'>
            <div style='font-size:2.5rem'>🤖</div>
            <div style='font-family:Orbitron;color:{ac};font-size:1.1rem;margin:0.5rem 0'>{top_a.replace("_"," ")}</div>
            <div style='font-family:Orbitron;font-size:2rem;color:#F5A623'>{top_p*100:.1f}%</div>
            <div style='color:#7BA3C4;font-size:0.8rem;letter-spacing:1px'>AI CONFIDENCE</div>
            <div style='color:#7BA3C4;font-size:0.8rem;margin-top:0.5rem'>
                Solar: {sk:.2f} kW | Battery: {snap["battery_level"]:.1f}%</div>
        </div>""",unsafe_allow_html=True)

    stats=db_get_system_stats(50)
    if stats:
        st.markdown("<div class='section'>DISTRIBUTION HISTORY</div>",unsafe_allow_html=True)
        df_h=pd.DataFrame(stats[::-1]); df_h["timestamp"]=pd.to_datetime(df_h["timestamp"])
        df_h["color"]=df_h["distribution_action"].map(ACTION_COLORS).fillna("#7BA3C4")
        fig_h=go.Figure(go.Scatter(x=df_h["timestamp"],y=df_h["solar_generation"],
            mode="markers",marker=dict(color=df_h["color"],size=10,opacity=0.8),
            text=df_h["distribution_action"].str.replace("_"," "),
            hovertemplate="<b>%{text}</b><br>Solar: %{y:.2f} kW<br>%{x}<extra></extra>"))
        dark_chart_layout(fig_h,280,yaxis=dict(gridcolor="#1E3A5F",title="Solar Gen (kW)"))
        st.plotly_chart(fig_h,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: BILLING
# ══════════════════════════════════════════════════════════════════════════════
def page_billing(user):
    uid=user["id"]; sector=user.get("sector","Residential")
    rate=SECTOR_RATES.get(sector,PRICE_PER_KWH)
    st.markdown("<h2>💳 BILLING & PAYMENTS</h2>",unsafe_allow_html=True)

    rows=db_get_user_energy(uid)
    if len(rows)<3:
        for _ in range(8): db_log_energy(uid,round(random.uniform(5,30),2))
        rows=db_get_user_energy(uid)

    total=sum(r["energy_consumed"] for r in rows)
    bill=calculate_bill(total,solar_fraction=0.55)
    payments=db_get_user_payments(uid)
    paid=sum(p["amount"] for p in payments if p["status"]=="paid")
    outstanding=max(0,bill["total_due"]-paid)

    st.markdown("<div class='section'>BILLING SUMMARY</div>",unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    kpi_card(c1,"⚡",f"{total:.1f} kWh","Total Usage","#F5A623")
    kpi_card(c2,"📋",f"${bill['total_due']:.2f}","Bill Total","#FF6B00")
    kpi_card(c3,"✅",f"${paid:.2f}","Amount Paid","#00FF94")
    kpi_card(c4,"⚠️",f"${outstanding:.2f}","Outstanding","#FF3D5A" if outstanding>0 else "#00FF94")

    st.markdown("<div class='section'>CURRENT INVOICE</div>",unsafe_allow_html=True)
    bc_,pc_=st.columns([1.2,1])
    with bc_:
        st.markdown("<div class='card'>",unsafe_allow_html=True)
        st.markdown(f"<h4 style='color:#00D4FF;margin-bottom:1rem'>INVOICE #{uid:04d}-{datetime.now().strftime('%Y%m')}</h4>",
                    unsafe_allow_html=True)
        for k,v in [("Account",user["username"]),("Sector",sector),
                    ("Billing Period",datetime.now().strftime("%B %Y")),
                    ("Energy Consumed",f"{bill['energy_consumed']:.2f} kWh"),
                    ("Unit Rate",f"${rate:.4f}/kWh"),("Gross Charge",f"${bill['gross_charge']:.2f}"),
                    ("Fixed Service Charge",f"${bill['fixed_charge']:.2f}"),
                    ("Solar Discount (55%)",f"-${bill['solar_discount']:.2f}")]:
            st.markdown(f"<div class='bill-line'><span style='color:#7BA3C4'>{k}</span><strong>{v}</strong></div>",
                        unsafe_allow_html=True)
        st.markdown(f"""<div style='display:flex;justify-content:space-between;padding:1rem 0 0'>
            <span style='font-family:Orbitron;font-size:0.95rem;color:#7BA3C4'>TOTAL DUE</span>
            <strong style='font-family:Orbitron;font-size:1.5rem;color:#F5A623'>${bill['total_due']:.2f}</strong>
        </div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    with pc_:
        st.markdown("<div class='card'>",unsafe_allow_html=True)
        st.markdown("<h4 style='color:#00D4FF'>MAKE A PAYMENT</h4>",unsafe_allow_html=True)
        pay_amt=st.number_input("Payment Amount ($)",min_value=0.01,
            max_value=float(bill["total_due"])+100,
            value=float(round(bill["total_due"],2)),step=0.01)
        method=st.radio("Payment Method",["💳 Credit Card","🏦 Bank Transfer","☀️ Solar Credits"],
            horizontal=True,label_visibility="collapsed")
        if st.button("✅ PAY NOW",use_container_width=True):
            db_create_payment(uid,pay_amt)
            st.success(f"✅ Payment of ${pay_amt:.2f} processed!")
            st.balloons(); st.rerun()
        if outstanding<=0:
            st.markdown("<div style='color:#00FF94;margin-top:1rem;text-align:center;font-family:Orbitron;font-size:0.85rem'>✓ ACCOUNT CLEAR</div>",
                        unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    if payments:
        st.markdown("<div class='section'>PAYMENT HISTORY</div>",unsafe_allow_html=True)
        df_p=pd.DataFrame(payments)
        df_p["date"]=pd.to_datetime(df_p["date"]).dt.strftime("%Y-%m-%d %H:%M")
        df_p["amount"]=df_p["amount"].apply(lambda x:f"${x:.2f}")
        df_p["status"]=df_p["status"].apply(lambda s:f"✅ {s.upper()}")
        st.dataframe(df_p[["id","amount","status","date"]],use_container_width=True,hide_index=True)

        df_ch=pd.DataFrame(payments); df_ch["date"]=pd.to_datetime(df_ch["date"])
        df_ch=df_ch.sort_values("date"); df_ch["cumulative"]=df_ch["amount"].cumsum()
        fig=go.Figure()
        fig.add_trace(go.Bar(x=df_ch["date"],y=df_ch["amount"],name="Payment",
            marker_color="#00D4FF",opacity=0.7))
        fig.add_trace(go.Scatter(x=df_ch["date"],y=df_ch["cumulative"],
            name="Cumulative",line=dict(color="#F5A623",width=2.5),yaxis="y2"))
        dark_chart_layout(fig,280,legend=dict(orientation="h",y=-0.3),
            yaxis2=dict(overlaying="y",side="right",showgrid=False,tickprefix="$"))
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.info("No payment history yet.")

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: WEATHER PANEL
# ══════════════════════════════════════════════════════════════════════════════
def page_weather(user, api_key, city):
    st.markdown("<h2>🌤 WEATHER & SOLAR ANALYSIS</h2>",unsafe_allow_html=True)
    w=fetch_weather(api_key,city)
    sk=predict_solar(w["solar_irradiance"],w["cloud_cover"],w["temperature"],w["humidity"])
    src="🌍 Live OWM" if w["source"]=="live" else "🔄 Simulated"
    st.markdown(f"<p style='color:#7BA3C4'>Location: <strong style='color:#F5A623'>{w.get('city',city)}</strong> | Source: <strong style='color:#00D4FF'>{src}</strong> | {datetime.now().strftime('%H:%M:%S')}</p>",
                unsafe_allow_html=True)

    st.markdown("<div class='section'>CURRENT CONDITIONS</div>",unsafe_allow_html=True)
    cond_lower=w["condition"].lower()
    emoji=next((v for k,v in {"sunny":"☀️","clear":"🌞","cloud":"☁️","rain":"🌧️",
                               "storm":"⛈️","snow":"❄️","fog":"🌫️"}.items() if k in cond_lower),"🌤")
    c1,c2,c3,c4,c5,c6=st.columns(6)
    kpi_card(c1,emoji,w["condition"],"Condition","#00D4FF")
    kpi_card(c2,"🌡️",f"{w['temperature']:.1f}°C","Temperature","#FF6B00")
    kpi_card(c3,"💧",f"{w['humidity']:.1f}%","Humidity","#00D4FF")
    kpi_card(c4,"☁️",f"{w['cloud_cover']:.1f}%","Cloud Cover","#7BA3C4")
    kpi_card(c5,"🌬️",f"{w.get('wind_speed',0):.1f} m/s","Wind Speed","#00FF94")
    kpi_card(c6,"🔆",f"{w['solar_irradiance']:.0f} W/m²","Irradiance","#F5A623")

    st.markdown("<div class='section'>24-HOUR SOLAR GENERATION FORECAST</div>",unsafe_allow_html=True)
    hours=list(range(24)); forecast=[]; irr_list=[]
    for h in hours:
        irr=cloud_to_irradiance(w["cloud_cover"],w["temperature"],h)
        kw=predict_solar(irr,w["cloud_cover"],w["temperature"],w["humidity"])
        forecast.append(kw); irr_list.append(irr)
    hlabels=[datetime.now().replace(hour=h,minute=0,second=0).strftime("%H:%M") for h in hours]
    cur_h=datetime.now().hour

    fig_f=go.Figure()
    fig_f.add_trace(go.Scatter(x=hlabels,y=forecast,name="Predicted kW",
        line=dict(color="#F5A623",width=3),fill="tozeroy",fillcolor="rgba(245,166,35,0.12)"))
    fig_f.add_trace(go.Scatter(x=hlabels,y=[v/100 for v in irr_list],name="Irradiance (scaled)",
        line=dict(color="#FF6B00",width=1.5,dash="dot"),yaxis="y2"))
    fig_f.add_vline(x=hlabels[cur_h],line_dash="dash",line_color="#00D4FF",
        annotation_text="NOW",annotation_font_color="#00D4FF")
    dark_chart_layout(fig_f,340,xaxis=dict(gridcolor="#1E3A5F",title="Hour"),
        yaxis=dict(gridcolor="#1E3A5F",title="kW"),
        yaxis2=dict(overlaying="y",side="right",showgrid=False,title="Irradiance (scaled)"),
        legend=dict(orientation="h",y=-0.25))
    st.plotly_chart(fig_f,use_container_width=True)

    st.markdown("<div class='section'>IRRADIANCE vs CLOUD SENSITIVITY</div>",unsafe_allow_html=True)
    cloud_range=list(range(0,101,5))
    irr_sens=[cloud_to_irradiance(c,w["temperature"],cur_h) for c in cloud_range]
    kw_sens=[predict_solar(irr,c,w["temperature"],w["humidity"]) for irr,c in zip(irr_sens,cloud_range)]
    s1,s2=st.columns(2)
    with s1:
        fig_si=go.Figure(go.Scatter(x=cloud_range,y=irr_sens,mode="lines+markers",
            line=dict(color="#F5A623",width=2.5),marker=dict(size=6,color="#FF6B00"),
            fill="tozeroy",fillcolor="rgba(245,166,35,0.08)"))
        fig_si.add_vline(x=w["cloud_cover"],line_dash="dash",line_color="#00D4FF",
            annotation_text=f"Now: {w['cloud_cover']:.0f}%",annotation_font_color="#00D4FF")
        dark_chart_layout(fig_si,280,xaxis=dict(gridcolor="#1E3A5F",title="Cloud Cover %"),
            yaxis=dict(gridcolor="#1E3A5F",title="W/m²"))
        fig_si.update_layout(title=dict(text="Cloud Cover → Irradiance",font=dict(color="#7BA3C4",family="Orbitron",size=11)))
        st.plotly_chart(fig_si,use_container_width=True)
    with s2:
        fig_sk=go.Figure(go.Scatter(x=cloud_range,y=kw_sens,mode="lines+markers",
            line=dict(color="#00D4FF",width=2.5),marker=dict(size=6,color="#00FF94"),
            fill="tozeroy",fillcolor="rgba(0,212,255,0.08)"))
        fig_sk.add_vline(x=w["cloud_cover"],line_dash="dash",line_color="#F5A623",
            annotation_text=f"Now: {sk:.2f} kW",annotation_font_color="#F5A623")
        dark_chart_layout(fig_sk,280,xaxis=dict(gridcolor="#1E3A5F",title="Cloud Cover %"),
            yaxis=dict(gridcolor="#1E3A5F",title="kW"))
        fig_sk.update_layout(title=dict(text="Cloud Cover → Solar Generation",font=dict(color="#7BA3C4",family="Orbitron",size=11)))
        st.plotly_chart(fig_sk,use_container_width=True)

    stats=db_get_system_stats(60)
    if stats:
        st.markdown("<div class='section'>HISTORICAL WEATHER METRICS</div>",unsafe_allow_html=True)
        df_w=pd.DataFrame(stats[::-1]); df_w["timestamp"]=pd.to_datetime(df_w["timestamp"])
        fig_w=go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w["timestamp"],y=df_w["temperature"],
            name="Temperature °C",line=dict(color="#FF6B00",width=2)))
        fig_w.add_trace(go.Scatter(x=df_w["timestamp"],y=df_w["humidity"],
            name="Humidity %",line=dict(color="#00D4FF",width=2,dash="dot")))
        fig_w.add_trace(go.Scatter(x=df_w["timestamp"],y=df_w["cloud_cover"],
            name="Cloud %",line=dict(color="#7BA3C4",width=2,dash="dashdot")))
        dark_chart_layout(fig_w,300,legend=dict(orientation="h",y=-0.25))
        st.plotly_chart(fig_w,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ══════════════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="Solar Microgrid AI",
        page_icon="☀️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    init_db()

    # ── Not logged in → show login page ──────────────────────────────────────
    if not st.session_state.get("logged_in"):
        st.session_state.setdefault("page","login")
        page_login()
        return

    user = st.session_state.user
    st.session_state.setdefault("page","dashboard")

    api_key, city = sidebar_nav(user)

    # ── Route to page ─────────────────────────────────────────────────────────
    page = st.session_state.page
    if   page == "dashboard":    page_dashboard(user, api_key, city)
    elif page == "user":         page_user(user)
    elif page == "admin":        page_admin(user)
    elif page == "distribution": page_distribution(user, api_key, city)
    elif page == "billing":      page_billing(user)
    elif page == "weather":      page_weather(user, api_key, city)
    else:                        page_dashboard(user, api_key, city)

if __name__ == "__main__":
    main()
