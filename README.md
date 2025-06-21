# GPT + Dropbox Asystent

Aplikacja GPT-4 analizuje pliki PDF i Excel z Dropboxa. Wystarczy wrzucić dokumenty do folderu `/chat-gpt-docs` w Twoim koncie Dropbox.

## Konfiguracja

1. Utwórz aplikację na https://www.dropbox.com/developers/apps
2. Wygeneruj Access Token
3. Wklej do `.streamlit/secrets.toml`:
```
DROPBOX_TOKEN = "twój_token"
OPENAI_API_KEY = "twój_api_key"
```

## Uruchomienie na Streamlit Cloud

1. Wrzuć repozytorium na GitHub
2. Wybierz je w Streamlit Cloud jako źródło
3. Gotowe!