# GPT + Dropbox Asystent (Manual Refresh FIX)

Aplikacja GPT-4 do analizy plików PDF/Excel z Dropboxa. Pliki pobierane są tylko po kliknięciu „Manual Refresh”.

✅ Ta wersja nie używa `st.experimental_rerun`, więc działa bez błędu na Streamlit Cloud.

## Jak używać:
1. Utwórz aplikację w Dropbox Developers
2. Zaznacz `files.content.read` i `files.metadata.read`
3. Wygeneruj token i wklej go do `.streamlit/secrets.toml`