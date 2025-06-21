import os
import streamlit as st
from io import BytesIO
from datetime import datetime

import dropbox
from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import tempfile

st.set_page_config(page_title="Dropbox GPT Asystent", layout="wide")
DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

dbx = dropbox.Dropbox(DROPBOX_TOKEN)
DROPBOX_FOLDER = "/chat-gpt-docs"

@st.cache_data(show_spinner=False, persist=True)
def list_dropbox_files(path):
    res = dbx.files_list_folder(path)
    return [entry for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)]

def extract_text_preview(docs, max_chars=1000):
    all_text = " ".join([d.page_content for d in docs])
    return all_text[:max_chars] + ("..." if len(all_text) > max_chars else "")

def process_files(selected_names):
    files = list_dropbox_files(DROPBOX_FOLDER)
    documents = []
    processed_files = []
    skipped_files = []

    for i, file in enumerate(files):
        if file.name not in selected_names:
            continue
        _, res = dbx.files_download(file.path_display)
        suffix = os.path.splitext(file.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(res.content)
            tmp_path = tmp_file.name

        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_path)
        elif suffix in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(tmp_path)
        else:
            skipped_files.append((file.name, "Nieobsługiwany format pliku"))
            continue

        try:
            docs = loader.load()
            for d in docs:
                d.metadata["source"] = file.name
            documents.extend(docs)
            preview = extract_text_preview(docs)
            st.markdown(f"**✅ Przetworzono plik:** `{file.name}`")
            with st.expander("🔍 Podgląd tekstu"):
                st.text(preview)
            processed_files.append(file.name)
        except Exception as e:
            skipped_files.append((file.name, f"Błąd przetwarzania: {str(e)}"))

    return documents, processed_files, skipped_files

st.title("📁 Asystent GPT z Dropbox – z podglądem i logiem")
st.markdown("🔄 Kliknij **Manual Refresh**, aby pobrać najnowsze pliki z Dropboxa.")

if "should_reload" not in st.session_state:
    st.session_state.should_reload = False

if st.button("🔄 Manual Refresh"):
    st.cache_data.clear()
    st.session_state.pop("qa_chain", None)
    st.session_state.should_reload = True
    st.success("✅ Odświeżono. Teraz kliknij „📥 Załaduj dokumenty”, by pobrać nowe pliki.")

files = list_dropbox_files(DROPBOX_FOLDER)
if not files:
    st.warning("Brak plików w folderze `/chat-gpt-docs` na Dropboxie.")
    st.stop()

file_names = [f.name for f in files]
selected_files = st.multiselect("📄 Wybierz pliki do analizy:", file_names, default=file_names)

if st.button("📥 Załaduj dokumenty") or st.session_state.get("should_reload", False):
    with st.spinner("⏳ Pobieranie i przetwarzanie..."):
        documents, processed_files, skipped_files = process_files(selected_files)
        if not documents:
            st.warning("Nie udało się załadować żadnych dokumentów.")
            st.stop()
        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        embedding = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(chunks, embedding)
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
        st.session_state.qa_chain = qa_chain
        st.session_state.should_reload = False
        st.success(f"✅ Załadowano {len(processed_files)} plików. Gotowe do pytań.")

        if skipped_files:
            st.warning("⚠️ Pominięto niektóre pliki:")
            for name, reason in skipped_files:
                st.markdown(f"- `{name}` – {reason}")

if "qa_chain" in st.session_state:
    query = st.text_input("✍️ Twoje pytanie")
    if query:
        with st.spinner("🧠 GPT analizuje..."):
            answer = st.session_state.qa_chain.run(query)
            st.markdown("### ✅ Odpowiedź:")
            st.write(answer)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"odpowiedz_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("Pytanie:\n" + query + "\n\nOdpowiedź:\n" + answer)

            with open(filename, "rb") as file:
                st.download_button(
                    label="💾 Pobierz odpowiedź jako TXT",
                    data=file,
                    file_name=filename,
                    mime="text/plain"
                )