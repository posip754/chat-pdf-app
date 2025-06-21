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

@st.cache_data(show_spinner=False, persist=True)
def download_selected_files(selected_names):
    files = list_dropbox_files(DROPBOX_FOLDER)
    documents = []
    total = len(selected_names)
    for i, file in enumerate(files):
        if file.name not in selected_names:
            continue
        _, res = dbx.files_download(file.path_display)
        suffix = os.path.splitext(file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(res.content)
            tmp_path = tmp_file.name
        if suffix.lower() == ".pdf":
            loader = PyPDFLoader(tmp_path)
        elif suffix.lower() in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(tmp_path)
        else:
            continue
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = file.name
        documents.extend(docs)
        st.progress((i + 1) / total)
    return documents

st.title("📁 Asystent GPT z Dropbox")
st.markdown("🔄 Kliknij **Manual Refresh**, aby pobrać najnowsze pliki z Dropboxa.")

if st.button("🔄 Manual Refresh"):
    st.cache_data.clear()
    st.session_state.pop("qa_chain", None)
    st.success("✅ Pamięć podręczna wyczyszczona. Kliknij ponownie „Załaduj dokumenty” aby pobrać z Dropboxa.")
    st.stop()

files = list_dropbox_files(DROPBOX_FOLDER)
if not files:
    st.warning("Brak plików w folderze `/chat-gpt-docs` na Dropboxie.")
    st.stop()

file_names = [f.name for f in files]
selected_files = st.multiselect("📄 Wybierz pliki do analizy:", file_names, default=file_names)

if st.button("📥 Załaduj dokumenty"):
    with st.spinner("⏳ Pobieranie i przetwarzanie..."):
        documents = download_selected_files(selected_files)
        if not documents:
            st.warning("Nie udało się załadować dokumentów.")
            st.stop()
        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        embedding = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(chunks, embedding)
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
        st.session_state.qa_chain = qa_chain
        st.success("✅ Dokumenty gotowe! Możesz teraz zadawać pytania.")

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