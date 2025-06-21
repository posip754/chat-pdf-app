import os
import streamlit as st
from io import BytesIO
from datetime import datetime

import dropbox
from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import tempfile

# Konfiguracja
st.set_page_config(page_title="Dropbox GPT Asystent", layout="wide")

# API Keys
DROPBOX_TOKEN = st.secrets["DROPBOX_TOKEN"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Nagłówek
st.markdown("### 📁 Analiza dokumentów z Dropbox + GPT-4")

# Połączenie z Dropbox
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# Folder w Dropbox
DROPBOX_FOLDER = "/chat-gpt-docs"

# Pobieranie plików z Dropbox
def list_dropbox_files(path):
    res = dbx.files_list_folder(path)
    return [entry for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)]

def download_file(entry):
    _, res = dbx.files_download(entry.path_display)
    suffix = os.path.splitext(entry.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(res.content)
        return tmp_file.name, entry.name

# Przetwarzanie dokumentów
documents = []
with st.spinner("🔄 Ładowanie plików z Dropbox..."):
    files = list_dropbox_files(DROPBOX_FOLDER)
    for file in files:
        path, original_name = download_file(file)
        if original_name.lower().endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif original_name.lower().endswith((".xlsx", ".xls")):
            loader = UnstructuredExcelLoader(path)
        else:
            continue
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = original_name
        documents.extend(docs)

if not documents:
    st.warning("📂 Brak plików PDF/Excel w folderze Dropbox `/chat-gpt-docs`.")
    st.stop()

# Przetwarzanie z GPT
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)
embedding = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(chunks, embedding)
llm = ChatOpenAI(model="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

# Interfejs pytania
st.success("✅ Dokumenty wczytane. Zadaj pytanie:")
query = st.text_input("✍️ Twoje pytanie", placeholder="Np. Jakie są koszty w dokumentach z Dropboxa?")

if query:
    with st.spinner("🧠 GPT analizuje..."):
        answer = qa_chain.run(query)
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