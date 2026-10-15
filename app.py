import streamlit as st
from src.agent import ShoppingAgent

st.set_page_config(page_title="Shopping Agent", page_icon="🛍️")
st.title("🛍️ Conversational Shopping Agent")

WELCOME = ("Hi! Tell me what you're looking for, for example: "
           "*'a lightweight waterproof running shoe under $80'*.")

# session_state: Streamlit har click par script dobara chalata hai,
# is liye agent aur chat history yahan save karte hain
if "agent" not in st.session_state:
    st.session_state.agent = ShoppingAgent()
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]

if st.sidebar.button("New conversation"):
    st.session_state.agent = ShoppingAgent()
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
    st.rerun()

# purani chat dikhao
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# naya message
if prompt := st.chat_input("What are you shopping for?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    reply = st.session_state.agent.chat(prompt)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)