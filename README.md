# Chat z przesyłanymi plikami (PDF i Excel) – FAISS

Aplikacja Streamlit z GPT-4 i LangChain, umożliwiająca analizowanie przesłanych plików PDF oraz Excel.
Działa z wektorową bazą FAISS, zgodną z hostingiem Streamlit Cloud.

## Uruchomienie online

1. Wgraj repozytorium na GitHub
2. Zaloguj się do https://streamlit.io/cloud
3. Kliknij "New app" i wybierz to repozytorium
4. W zakładce "Secrets" dodaj:
```
OPENAI_API_KEY = "sk-..."
```