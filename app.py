import os
import streamlit as st
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# Konfiguracja wyglądu
st.set_page_config(page_title="Dokumenty AI", page_icon="📄", layout="wide")

# API Key
openai_api_key = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = openai_api_key

# Tytuł i opis
col1, col2 = st.columns([1, 6])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Apple_logo_black.svg/1024px-Apple_logo_black.svg.png", width=40)
with col2:
    st.markdown("### **Asystent AI do dokumentów**")
    st.markdown("_Szybka analiza plików PDF i Excel dzięki GPT-4_")

# Folder z dokumentami
doc_folder = "dokumenty"
doc_files = [f for f in os.listdir(doc_folder) if f.endswith((".pdf", ".xlsx", ".xls"))]

if not doc_files:
    st.warning("📂 Brak dokumentów do analizy. Dodaj pliki PDF lub Excel do folderu 'dokumenty/'.")
    st.stop()

# Ładowanie dokumentów
with st.spinner("🔄 Ładowanie dokumentów..."):
    documents = []
    for file in doc_files:
        path = os.path.join(doc_folder, file)
        if file.endswith(".pdf"):
            loader = PyPDFLoader(path)
        else:
            loader = UnstructuredExcelLoader(path)
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = file
        documents.extend(docs)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

st.success("✅ Gotowe! Możesz teraz zadawać pytania.")

query = st.text_input("✍️ Twoje pytanie", placeholder="Np. Jakie są koszty w plikach?")

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

st.markdown("---")
st.caption("© 2024 AI Dokumenty – Aplikacja demo stworzona w stylu Apple • powered by GPT-4")