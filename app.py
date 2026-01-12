import streamlit as st
import requests, os, json, uuid
from dotenv import load_dotenv
from pypdf import PdfReader
from duckduckgo_search import DDGS
from PIL import Image

# ================= ENV =================
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    st.error("Missing GROQ_API_KEY")
    st.stop()

URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
DB = "chats.json"

# ================= DATABASE =================
def load_db():
    if not os.path.exists(DB):
        return {}
    return json.load(open(DB))

def save_db(d):
    json.dump(d, open(DB,"w"), indent=2)

# ================= WEB =================
def web_search(q):
    out=""
    with DDGS() as d:
        for r in d.text(q, max_results=5):
            out += r["body"]+"\n"
    return out

# ================= LLM =================
def ask(messages):
    r = requests.post(
        URL,
        headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"},
        json={"model":MODEL,"messages":messages,"temperature":0.7}
    )
    return r.json()["choices"][0]["message"]["content"]

# ================= UI CONFIG =================
st.set_page_config("Thinkr","🚀",layout="wide")

st.markdown("""
<style>

/* ===== AI UNIVERSE BACKGROUND ===== */
.stApp::before{
    content:"";
    position:fixed;
    inset:0;
    background:
        radial-gradient(circle at 20% 20%, #3b82f633, transparent 40%),
        radial-gradient(circle at 80% 30%, #a855f733, transparent 40%),
        radial-gradient(circle at 40% 80%, #22d3ee33, transparent 40%);
    filter: blur(90px);
    z-index:-1;
    animation: floatbg 20s ease-in-out infinite alternate;
}
@keyframes floatbg{
    0%{transform:translate(0,0)}
    100%{transform:translate(-40px,40px)}
}

/* ===== BODY ===== */
body,.stApp{
    background:radial-gradient(circle at top,#020617,#020617);
    color:white;
}

/* ===== SIDEBAR GLASS ===== */
[data-testid=stSidebar]{
    background:rgba(2,6,23,0.6);
    backdrop-filter:blur(22px);
    border-right:1px solid rgba(255,255,255,0.12);
    box-shadow:10px 0 40px rgba(0,0,0,0.7);
}

/* ===== CHAT BUBBLES ===== */
.stChatMessage{
    background:rgba(255,255,255,0.06);
    backdrop-filter:blur(18px);
    border-radius:20px;
    border:1px solid rgba(255,255,255,0.12);
    box-shadow:0 10px 40px rgba(0,0,0,0.6);
    animation: floatCard 6s ease-in-out infinite alternate;
}
@keyframes floatCard{
    from{transform:translateY(0px)}
    to{transform:translateY(-6px)}
}

/* ===== INPUT BAR ===== */
.stChatInputContainer{
    background:rgba(15,23,42,0.55);
    backdrop-filter:blur(22px);
    border-radius:28px;
    border:1px solid rgba(255,255,255,0.25);
    box-shadow:0 0 30px rgba(99,102,241,0.35);
    transition:0.3s ease;
}
.stChatInputContainer:focus-within{
    box-shadow:0 0 50px rgba(139,92,246,0.8);
}

/* ===== BUTTONS ===== */
button{
    background:rgba(255,255,255,0.06)!important;
    border:1px solid rgba(255,255,255,0.15)!important;
    border-radius:14px!important;
    transition:0.3s ease;
}
button:hover{
    box-shadow:0 0 20px #818cf8;
    transform:translateY(-2px);
}

/* ===== TITLE ===== */
h1{
    font-size:56px;
    font-weight:900;
    background:linear-gradient(90deg,#38bdf8,#a855f7);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    text-shadow:0 0 40px #6366f1aa;
}

</style>
""",unsafe_allow_html=True)

st.title("🧠 Thinkr.ai")
st.caption("PDF • Vision • Web • Memory")

# ================= INIT =================
db = load_db()
if "chat_id" not in st.session_state:
    cid=str(uuid.uuid4())
    db[cid]={"title":"New Chat","messages":[{"role":"system","content":"You are Thinkr, an ultra intelligent AI."}]}
    save_db(db)
    st.session_state.chat_id=cid

chat = db[st.session_state.chat_id]

# ================= SIDEBAR =================
st.sidebar.title("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    cid=str(uuid.uuid4())
    db[cid]={"title":"New Chat","messages":[{"role":"system","content":"You are Thinkr."}]}
    save_db(db)
    st.session_state.chat_id=cid
    st.rerun()

for cid in db:
    if st.sidebar.button(db[cid]["title"], key=cid):
        st.session_state.chat_id=cid
        st.rerun()

st.sidebar.markdown("---")
new_title = st.sidebar.text_input("✏ Rename Chat", chat["title"])
if new_title:
    chat["title"]=new_title
    save_db(db)

if st.sidebar.button("🗑 Delete Chat"):
    del db[st.session_state.chat_id]
    save_db(db)
    st.session_state.chat_id=list(db.keys())[0]
    st.rerun()

# ================= CHAT =================
for m in chat["messages"][1:]:
    with st.chat_message(m["role"], avatar="🚀" if m["role"]=="assistant" else "🧑‍🚀"):
        st.write(m["content"])

# ================= TOOL BAR =================
c1,c2,c3 = st.columns([1,1,2])
with c1:
    pdf = st.file_uploader("📄 PDF", type="pdf")
with c2:
    img = st.file_uploader("🖼 Image", type=["png","jpg","jpeg"])
with c3:
    web = st.text_input("🌐 Web Search")

if pdf:
    text=""
    for p in PdfReader(pdf).pages:
        text+=p.extract_text()
    chat["messages"].append({"role":"system","content":"PDF:\n"+text[:8000]})

if web:
    chat["messages"].append({"role":"system","content":"Web:\n"+web_search(web)})

# ================= INPUT =================
prompt = st.chat_input("Ask Thinkr anything…")
if prompt:
    chat["messages"].append({"role":"user","content":prompt})
    st.chat_message("user", avatar="🧑‍🚀").write(prompt)

    reply = ask(chat["messages"])
    chat["messages"].append({"role":"assistant","content":reply})
    st.chat_message("assistant", avatar="🚀").write(reply)

    if chat["title"]=="New Chat":
        chat["title"]=ask([{"role":"system","content":"Give a short chat title"},{"role":"user","content":prompt}])

    save_db(db)
