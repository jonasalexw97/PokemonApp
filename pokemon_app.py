import streamlit as st
import psycopg2
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


def back_to_home():
    if st.button("⬅️ Zurück zum Menü"):
        st.session_state["page"] = "🏠 Home"
        st.rerun()


# =========================================================
# DB
# =========================================================
conn = psycopg2.connect(
    dbname="pokemon_db",
    user="postgres",
    password="1234",
    host="localhost",
    port="5434"
)
cur = conn.cursor()

cur.execute("SELECT id, name FROM sets")
set_dict = {name: id for id, name in cur.fetchall()}
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
# HOME (verbessertes Layout)
# =========================================================
if page == "🏠 Home":
    st.markdown("## 👋 Willkommen")

    st.markdown("### Wähle einen Bereich")

    col1, col2, col3 = st.columns(3)

    # ---------------- CARD 1 ----------------
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg,#2b2b3d,#1f1f2e);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            cursor: pointer;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
        ">
            <div style="font-size:50px;">🔍</div>
            <h2>Karten suchen</h2>
            <p style="opacity:0.7;">Pokémon Karten entdecken</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if st.button("▶ Öffnen", key="home_search"):
            st.session_state["page"] = "🔍 Karten suchen"
            st.rerun()

    # ---------------- CARD 2 ----------------
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg,#2b2b3d,#1f1f2e);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
        ">
            <div style="font-size:50px;">📚</div>
            <h2>Bibliothek</h2>
            <p style="opacity:0.7;">Deine Sammlung verwalten</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if st.button("▶ Öffnen", key="home_library"):
            st.session_state["page"] = "📚 Bibliothek"
            st.rerun()

    # ---------------- CARD 3 ----------------
    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg,#2b2b3d,#1f1f2e);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
        ">
            <div style="font-size:50px;">📊</div>
            <h2>Portfolio</h2>
            <p style="opacity:0.7;">Wert deiner Karten</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if st.button("▶ Öffnen", key="home_portfolio"):
            st.session_state["page"] = "📊 Portfolio"
            st.rerun()
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

            if selected and selected.get("id") == c["id"]:

                st.markdown("---")

                # =================================================
                # STEP 1: ZUSTAND + VARIANTE
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

                    st.markdown(f"""
                    <div style="
                        padding:10px;
                        border-radius:10px;
                        background:#1f1f2e;
                        margin-top:10px;
                        text-align:center;
                    ">
                        Zustand: <b>{condition}</b> | Variante: <b>{variant}</b>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Weiter", key=f"n1_{c['id']}"):
                        st.session_state["temp_condition"] = condition
                        st.session_state["temp_variant"] = variant
                        st.session_state["step"] = 2
                        st.rerun()

                # =================================================
                # STEP 2: KAUFPREIS
                # =================================================
                elif st.session_state["step"] == 2:

                    st.session_state["purchase_price"] = st.number_input(
                        "Kaufpreis",
                        min_value=0.0,
                        key=f"b_{c['id']}"
                    )

                    if st.button("Weiter", key=f"n2_{c['id']}"):
                        st.session_state["step"] = 3
                        st.rerun()

                # =================================================
                # STEP 3: AKTUELLER PREIS + SPEICHERN
                # =================================================
                elif st.session_state["step"] == 3:

                    current_price = st.number_input(
                        "Aktueller Preis",
                        min_value=0.0,
                        key=f"c_{c['id']}"
                    )

                    if st.button("Speichern", key=f"s_{c['id']}"):

                        # Card sichern
                        cur.execute("""
                            INSERT INTO cards (id, name, image_url)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (
                            c["id"],
                            c["name"],
                            c["images"]["small"]
                        ))

                        # Collection speichern
                        cur.execute("""
                            INSERT INTO collection 
                            (card_id, purchase_price, current_price, condition, variant, purchase_date)
                            VALUES (%s,%s,%s,%s,%s,NOW())
                        """, (
                            c["id"],
                            st.session_state["purchase_price"],
                            current_price,
                            st.session_state.get("temp_condition", "Good"),
                            st.session_state.get("temp_variant", "Normal")
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
        "Sortieren nach",
        ["Aktueller Preis ↓", "Aktueller Preis ↑", "Kaufpreis ↓", "Kaufpreis ↑"]
    )

    order_sql = {
        "Aktueller Preis ↓": "col.current_price DESC",
        "Aktueller Preis ↑": "col.current_price ASC",
        "Kaufpreis ↓": "col.purchase_price DESC",
        "Kaufpreis ↑": "col.purchase_price ASC"
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
            (col.current_price - col.purchase_price) AS profit
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
            st.write(f"**{name}**")
            st.write(f"Zustand: {condition}")
            st.write(f"Variante: {variant}")
            st.write(f"Kaufpreis: {buy} €")
            st.write(f"Aktueller Preis: {current} €")
            st.write(("🟢 Gewinn: " if profit >= 0 else "🔴 Verlust: "), round(profit, 2))

        with col3:
            if st.button("🗑️ Löschen", key=f"del_{col_id}"):

                cur.execute("DELETE FROM collection WHERE id=%s", (col_id,))
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

    c1, c2, c3 = st.columns(3)

    c1.metric("Karten", count)
    c2.metric("Investiert", f"{invested:.2f} €")
    c3.metric("Wert", f"{value:.2f} €")

    st.metric("Gewinn", f"{profit:.2f} €")