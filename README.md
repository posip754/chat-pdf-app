# GPT + Dropbox Asystent (Stable Session)

Ta wersja aplikacji GPT-4 zachowuje przetworzone dokumenty i łańcuch zapytań (`qa_chain`) w `st.session_state`, dzięki czemu nie traci ich po wpisaniu pytania.

✅ Stabilne działanie formularza zapytania
✅ Brak resetowania interfejsu przy wpisaniu pytania

## Użycie:
1. Wgraj aplikację do Streamlit Cloud
2. Dodaj `OPENAI_API_KEY` i `DROPBOX_TOKEN` do `.streamlit/secrets.toml`