
import os
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="Chat z przesyłanymi plikami", layout="wide")

from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from datetime import datetime
import tempfile

openai_api_key = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = openai_api_key

st.title("📤 Chat z przesyłanymi plikami PDF i Excel")

uploaded_files = st.file_uploader("Prześlij pliki PDF lub Excel", type=["pdf", "xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("🔄 Przetwarzanie przesłanych plików..."):
        documents = []

        for uploaded_file in uploaded_files:
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name

            if suffix.lower() == ".pdf":
                loader = PyPDFLoader(tmp_file_path)
            elif suffix.lower() in [".xlsx", ".xls"]:
                loader = UnstructuredExcelLoader(tmp_file_path)
            else:
                continue

            docs = loader.load()
            for d in docs:
                d.metadata["source"] = uploaded_file.name
            documents.extend(docs)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents)
        embedding = OpenAIEmbeddings()
        vectorstore = Chroma.from_documents(chunks, embedding)
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

    st.success("✅ Gotowe! Możesz teraz zadawać pytania do przesłanych plików.")
    query = st.text_input("🗣️ Twoje pytanie:", placeholder="Np. Jakie są koszty w przesłanych plikach?")

    if query:
        with st.spinner("🔎 GPT analizuje..."):
            answer = qa_chain.run(query)
            st.success("🧠 Odpowiedź:")
            st.write(answer)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"odpowiedz_{timestamp}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("Pytanie:\n" + query + "\n\nOdpowiedź:\n" + answer)

            with open(filename, "rb") as file:
                st.download_button(
                    label="💾 Pobierz odpowiedź jako plik .txt",
                    data=file,
                    file_name=filename,
                    mime="text/plain"
                )
else:
    st.info("⬆️ Prześlij pliki PDF lub Excel, aby rozpocząć.")
