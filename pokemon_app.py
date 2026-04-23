import streamlit as st
import sqlite3
import requests

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Pokémon App", layout="wide")

# =========================================================
# SESSION STATE
# =========================================================
if "init" not in st.session_state:
    st.session_state.update({
        "page": "🏠 Home",
        "selected_card": None,
        "step": 1,
        "purchase_price": 0.0,
        "set_cards": [],
    })
    st.session_state["init"] = True

# =========================================================
# API
# =========================================================
def get_cards(search=None, set_name=None):
    try:
        url = "https://api.pokemontcg.io/v2/cards?"
        q = []

        if search:
            q.append(f'name:"{search}"')

        if set_name and set_name != "ALL":
            q.append(f'set.name:"{set_name}"')

        if q:
            url += "q=" + " ".join(q)

        r = requests.get(url, timeout=20)
        return r.json().get("data", [])

    except:
        return []

# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0e0e10, #1a1a1f);
    color: white;
}
.block-container {
    padding-top: 1rem;
}
button:hover {
    transform: scale(1.02);
    transition: 0.2s;
}
</style>
""", unsafe_allow_html=True)

st.title("🃏 Pokémon App")

# =========================================================
# BACK
# =========================================================
def back_to_home():
    if st.button("⬅️ Zurück zum Menü"):
        st.session_state["page"] = "🏠 Home"
        st.rerun()

# =========================================================
# DB
# =========================================================
conn = sqlite3.connect("pokemon.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    name TEXT,
    image_url TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS collection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT,
    purchase_price REAL,
    current_price REAL,
    condition TEXT,
    variant TEXT,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
""")

conn.commit()

# =========================================================
# LOAD SETS
# =========================================================
cur.execute("SELECT id, name FROM sets")
rows = cur.fetchall()

if len(rows) == 0:
    data = requests.get("https://api.pokemontcg.io/v2/sets").json()["data"]

    for s in data:
        cur.execute("INSERT OR IGNORE INTO sets (name) VALUES (?)", (s["name"],))

    conn.commit()
    cur.execute("SELECT id, name FROM sets")
    rows = cur.fetchall()

set_dict = {name: id for id, name in rows}
set_options = ["ALL"] + list(set_dict.keys())

# =========================================================
# NAV
# =========================================================
with st.sidebar:
    st.markdown("## 🧭 Menü")

    for label in ["🏠 Home", "🔍 Karten suchen", "📚 Bibliothek", "📊 Portfolio"]:
        if st.button(label):
            st.session_state["page"] = label
            st.rerun()

page = st.session_state["page"]

# =========================================================
# HOME (CLICKABLE BIG CARDS)
# =========================================================
if page == "🏠 Home":

    st.markdown("## 👋 Willkommen")
    st.markdown("### Wähle einen Bereich")

    col1, col2, col3 = st.columns(3)

    def card(icon, title, desc, target, key):
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg,#2b2b3d,#1f1f2e);
            padding: 50px;
            border-radius: 25px;
            text-align: center;
            cursor: pointer;
            box-shadow: 0 8px 30px rgba(0,0,0,0.5);
        ">
            <div style="font-size:60px;">{icon}</div>
            <h2>{title}</h2>
            <p style="opacity:0.7;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Öffnen", key=key):
            st.session_state["page"] = target
            st.rerun()

    with col1:
        card("🔍", "Karten suchen", "Pokémon Karten entdecken", "🔍 Karten suchen", "h1")

    with col2:
        card("📚", "Bibliothek", "Deine Sammlung", "📚 Bibliothek", "h2")

    with col3:
        card("📊", "Portfolio", "Dein Kartenwert", "📊 Portfolio", "h3")

# =========================================================
# SEARCH
# =========================================================
elif page == "🔍 Karten suchen":

    back_to_home()
    st.subheader("🔍 Suche")

    search = st.text_input("Kartenname")
    selected_set = st.selectbox("Set", set_options)

    if st.button("Suchen"):
        st.session_state["set_cards"] = get_cards(search, selected_set)

    cards = st.session_state.get("set_cards", [])
    cols = st.columns(4)

    for i, c in enumerate(cards):

        with cols[i % 4]:

            st.image(c["images"]["small"], use_container_width=True)
            st.caption(f"{c['name']} #{c.get('number','?')}")

            if st.button("👉 Auswählen", key=f"sel_{c['id']}"):
                st.session_state["selected_card"] = c
                st.session_state["step"] = 1
                st.rerun()

            selected = st.session_state.get("selected_card")

            if selected and selected["id"] == c["id"]:

                st.markdown("---")

                # =================================================
                # STEP 1 (FIXED + PLAYED ADDED)
                # =================================================
                if st.session_state["step"] == 1:

                    condition = st.selectbox(
                        "Zustand",
                        ["Poor", "Light Played", "Played", "Good", "Excellent", "Near Mint"],
                        key=f"cond_{c['id']}"
                    )

                    variant = st.radio(
                        "Variante",
                        ["Normal", "Holo", "Reverse Holo"],
                        horizontal=True,
                        key=f"var_{c['id']}"
                    )

                    if st.button("Weiter", key=f"n1_{c['id']}"):
                        st.session_state["temp_condition"] = condition
                        st.session_state["temp_variant"] = variant
                        st.session_state["step"] = 2
                        st.rerun()

                elif st.session_state["step"] == 2:

                    st.session_state["purchase_price"] = st.number_input(
                        "Kaufpreis",
                        min_value=0.0,
                        key=f"b_{c['id']}"
                    )

                    if st.button("Weiter", key=f"n2_{c['id']}"):
                        st.session_state["step"] = 3
                        st.rerun()

                elif st.session_state["step"] == 3:

                    current_price = st.number_input(
                        "Aktueller Preis",
                        min_value=0.0,
                        key=f"c_{c['id']}"
                    )

                    if st.button("Speichern", key=f"s_{c['id']}"):

                        cur.execute("""
                        INSERT OR IGNORE INTO cards (id, name, image_url)
                        VALUES (?, ?, ?)
                        """, (c["id"], c["name"], c["images"]["small"]))

                        cur.execute("""
                        INSERT INTO collection
                        (card_id, purchase_price, current_price, condition, variant, purchase_date)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            c["id"],
                            st.session_state["purchase_price"],
                            current_price,
                            st.session_state["temp_condition"],
                            st.session_state["temp_variant"]
                        ))

                        conn.commit()

                        st.success("Gespeichert!")

                        st.session_state.update({
                            "selected_card": None,
                            "step": 1
                        })

                        st.rerun()

# =========================================================
# BIBLIOTHEK
# =========================================================
elif page == "📚 Bibliothek":

    back_to_home()
    st.subheader("📚 Sammlung")

    sort_option = st.selectbox(
        "Sortieren",
        ["Aktueller Preis ↓", "Aktueller Preis ↑", "Kaufpreis ↓", "Kaufpreis ↑"]
    )

    order_sql = {
        "Aktueller Preis ↓": "current_price DESC",
        "Aktueller Preis ↑": "current_price ASC",
        "Kaufpreis ↓": "purchase_price DESC",
        "Kaufpreis ↑": "purchase_price ASC"
    }[sort_option]

    cur.execute(f"""
        SELECT
            col.id,
            c.name,
            c.image_url,
            col.purchase_price,
            col.current_price,
            col.condition,
            col.variant,
            (col.current_price - col.purchase_price)
        FROM collection col
        JOIN cards c ON col.card_id = c.id
        ORDER BY {order_sql}
    """)

    rows = cur.fetchall()

    for col_id, name, img, buy, current, condition, variant, profit in rows:

        col1, col2, col3 = st.columns([1.5, 4, 1])

        with col1:
            if img:
                st.image(img, width=170)

        with col2:
            st.write(name)
            st.write(condition)
            st.write(variant)
            st.write(f"{buy} → {current}")
            st.write("🟢" if profit >= 0 else "🔴", round(profit, 2))

        with col3:
            if st.button("🗑️ Löschen", key=f"del_{col_id}"):

                cur.execute("DELETE FROM collection WHERE id=?", (col_id,))
                conn.commit()
                st.rerun()

# =========================================================
# PORTFOLIO
# =========================================================
elif page == "📊 Portfolio":

    back_to_home()
    st.subheader("📊 Portfolio")

    cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(purchase_price),0),
            COALESCE(SUM(current_price),0),
            COALESCE(SUM(current_price - purchase_price),0)
        FROM collection
    """)

    count, invested, value, profit = cur.fetchone()

    st.metric("Karten", count)
    st.metric("Investiert", f"{invested:.2f} €")
    st.metric("Wert", f"{value:.2f} €")
    st.metric("Gewinn", f"{profit:.2f} €")
