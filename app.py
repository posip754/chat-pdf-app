
import os
import streamlit as st

st.set_page_config(page_title="Chat z PDF i Excel", layout="wide")

from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from datetime import datetime

# 🔐 API Key z sekcji "Secrets" na Streamlit Cloud
openai_api_key = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = openai_api_key

doc_folder = "dokumenty"

def load_documents(selected_files):
    documents = []
    for filename in selected_files:
        path = os.path.join(doc_folder, filename)
        if filename.lower().endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif filename.lower().endswith((".xlsx", ".xls")):
            loader = UnstructuredExcelLoader(path)
        else:
            continue
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = filename
        documents.extend(docs)
    return documents

doc_files = [f for f in os.listdir(doc_folder) if f.endswith((".pdf", ".xlsx", ".xls"))]

st.title("📊 ChatGPT z PDF i Excel")
st.markdown("Wybierz pliki do przeszukania:")

selected_files = st.multiselect("📄 Pliki:", doc_files, default=doc_files)

if selected_files:
    with st.spinner("🔄 Przetwarzanie dokumentów..."):
        docs = load_documents(selected_files)
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        embedding = OpenAIEmbeddings()
        vectorstore = Chroma.from_documents(chunks, embedding)
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

    query = st.text_input("🧠 Twoje pytanie:", placeholder="Np. Jakie są koszty w 2023?")
    if query:
        with st.spinner("🔎 Szukam odpowiedzi..."):
            answer = qa_chain.run(query)
            st.success("✅ Odpowiedź:")
            st.write(answer)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"odpowiedz_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("Pytanie:\n" + query + "\n\nOdpowiedź:\n" + answer)

            with open(filename, "rb") as file:
                st.download_button(
                    label="💾 Pobierz odpowiedź jako .txt",
                    data=file,
                    file_name=filename,
                    mime="text/plain"
                )
else:
    st.info("⬆️ Wrzuć pliki PDF lub Excel do folderu 'dokumenty'.")
