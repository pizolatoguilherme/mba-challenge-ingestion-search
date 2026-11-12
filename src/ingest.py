import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from search import get_collection_name, get_vector_store

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = os.getenv("PDF_PATH", "document.pdf").strip().strip("'\"") or "document.pdf"


def resolve_pdf_path() -> Path:
    path = Path(PDF_PATH)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.is_file():
        raise FileNotFoundError(f"PDF não encontrado: {path}")
    return path


def ingest_pdf():
    pdf_path = resolve_pdf_path()
    print(f"Carregando PDF: {pdf_path}")
    pages = PyPDFLoader(str(pdf_path)).load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(pages)
    if not chunks:
        raise RuntimeError("Nenhum conteúdo extraído do PDF.")

    documents = [
        Document(
            page_content=chunk.page_content,
            metadata={k: v for k, v in chunk.metadata.items() if v not in (None, "")},
        )
        for chunk in chunks
    ]
    ids = [f"doc-{i}" for i in range(len(documents))]

    collection = get_collection_name()
    print(f"{len(pages)} páginas -> {len(documents)} chunks. Gerando embeddings e salvando em '{collection}'...")

    # pre_delete_collection=True torna a ingestão idempotente (recria a collection a cada execução)
    store = get_vector_store(pre_delete_collection=True)
    store.add_documents(documents=documents, ids=ids)

    print("Ingestão concluída com sucesso.")


if __name__ == "__main__":
    ingest_pdf()
