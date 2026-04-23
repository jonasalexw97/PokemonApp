import streamlit as st
import requests
from supabase import create_client, Client

# =========================================================
# SUPABASE CONNECT
# =========================================================
SUPABASE_URL = "https://nnfbikdijkzjdcaltluk.supabase.co"
SUPABASE_KEY = "sb_publishable_nFVFz7-KZj5LfUPFtONjmw_ilxti7Lt"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# LOAD SETS (SUPABASE)
# =========================================================
sets = supabase.table("sets").select("*").execute().data

if not sets:
    data = requests.get("https://api.pokemontcg.io/v2/sets").json()["data"]

    for s in data:
        supabase.table("sets").insert({"name": s["name"]}).execute()

    sets = supabase.table("sets").select("*").execute().data

set_options = ["ALL"] + [s["name"] for s in sets]

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
# HOME
# =========================================================
if page == "🏠 Home":

    st.markdown("## 👋 Willkommen")

    col1, col2, col3 = st.columns(3)

    def card(icon, title, desc, target, key):
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg,#2b2b3d,#1f1f2e);
            padding: 50px;
            border-radius: 25px;
            text-align: center;
        ">
            <div style="font-size:60px;">{icon}</div>
            <h2>{title}</h2>
            <p>{desc}</p>
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
# SEARCH (SUPABASE SAVE)
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

                        supabase.table("cards").upsert({
                            "id": c["id"],
                            "name": c["name"],
                            "image_url": c["images"]["small"]
                        }).execute()

                        supabase.table("collection").insert({
                            "card_id": c["id"],
                            "purchase_price": st.session_state["purchase_price"],
                            "current_price": current_price,
                            "condition": st.session_state["temp_condition"],
                            "variant": st.session_state["temp_variant"]
                        }).execute()

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

    # -----------------------------
    # SORT OPTION
    # -----------------------------
    sort_option = st.selectbox(
        "Sortieren",
        ["Aktueller Preis ↓", "Aktueller Preis ↑", "Gewinn ↓", "Gewinn ↑"]
    )

    # -----------------------------
    # DATA LOAD
    # -----------------------------
    collection = supabase.table("collection").select("*").execute().data
    cards = supabase.table("cards").select("*").execute().data

    # Map für schnelle Card-Zuordnung
    card_map = {c["id"]: c for c in cards}

    # -----------------------------
    # SORT LOGIC
    # -----------------------------
    def profit(x):
        return x["current_price"] - x["purchase_price"]

    if sort_option == "Aktueller Preis ↓":
        collection.sort(key=lambda x: x["current_price"], reverse=True)

    elif sort_option == "Aktueller Preis ↑":
        collection.sort(key=lambda x: x["current_price"])

    elif sort_option == "Gewinn ↓":
        collection.sort(key=profit, reverse=True)

    elif sort_option == "Gewinn ↑":
        collection.sort(key=profit)

    # -----------------------------
    # DISPLAY
    # -----------------------------
    for row in collection:

        card = card_map.get(row["card_id"])

        col1, col2, col3 = st.columns([2, 5, 1])

        with col1:
            if card:
                st.image(card["image_url"], width=180)

        with col2:
            st.write(card["name"] if card else "Unknown Card")
            st.write(f"Zustand: {row['condition']}")
            st.write(f"Variante: {row['variant']}")
            st.write(f"{row['purchase_price']} € → {row['current_price']} €")

            profit_value = row["current_price"] - row["purchase_price"]
            st.write("🟢" if profit_value >= 0 else "🔴", round(profit_value, 2))

        with col3:
            if st.button("🗑️", key=f"del_{row['id']}"):
                supabase.table("collection").delete().eq("id", row["id"]).execute()
                st.rerun()

# =========================================================
# PORTFOLIO
# =========================================================
elif page == "📊 Portfolio":

    back_to_home()
    st.subheader("📊 Portfolio")

    data = supabase.table("collection").select("*").execute().data

    count = len(data)
    invested = sum(x["purchase_price"] for x in data)
    value = sum(x["current_price"] for x in data)
    profit = value - invested

    st.metric("Karten", count)
    st.metric("Investiert", f"{invested:.2f} €")
    st.metric("Wert", f"{value:.2f} €")
    st.metric("Gewinn", f"{profit:.2f} €")
