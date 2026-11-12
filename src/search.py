import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

TOP_K = 10
SUPPORTED_PROVIDERS = ("openai", "gemini")


# ---------------------------------------------------------------------------
# Provedores (OpenAI / Gemini), selecionados via variável LLM_PROVIDER
# ---------------------------------------------------------------------------

def _require(var_name: str) -> str:
    value = os.getenv(var_name, "").strip().strip("'\"")
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória não definida: {var_name}")
    return value


def get_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise RuntimeError(
            f"LLM_PROVIDER inválido: '{provider}'. Use um de: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    return provider


def get_embeddings():
    if get_provider() == "openai":
        from langchain_openai import OpenAIEmbeddings

        _require("OPENAI_API_KEY")
        return OpenAIEmbeddings(model=_require("OPENAI_EMBEDDING_MODEL"))

    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    _require("GOOGLE_API_KEY")
    return GoogleGenerativeAIEmbeddings(model=_require("GOOGLE_EMBEDDING_MODEL"))


def get_llm():
    if get_provider() == "openai":
        from langchain_openai import ChatOpenAI

        _require("OPENAI_API_KEY")
        return ChatOpenAI(model=_require("OPENAI_LLM_MODEL"), temperature=0)

    from langchain_google_genai import ChatGoogleGenerativeAI

    _require("GOOGLE_API_KEY")
    return ChatGoogleGenerativeAI(model=_require("GOOGLE_LLM_MODEL"), temperature=0)


def get_collection_name() -> str:
    """Uma collection por provedor, evitando conflito de dimensão entre modelos de embedding."""
    base = os.getenv("PG_VECTOR_COLLECTION_NAME", "").strip().strip("'\"") or "documents"
    return f"{base}_{get_provider()}"


def get_vector_store(pre_delete_collection: bool = False):
    from langchain_postgres import PGVector

    return PGVector(
        embeddings=get_embeddings(),
        collection_name=get_collection_name(),
        connection=_require("DATABASE_URL"),
        use_jsonb=True,
        pre_delete_collection=pre_delete_collection,
    )


# ---------------------------------------------------------------------------
# Busca + prompt + LLM
# ---------------------------------------------------------------------------

def search_prompt(question=None):
    """Monta a chain de RAG. Retorna a chain, ou a resposta se `question` for informada.

    Retorna None se não for possível inicializar (variáveis de ambiente, banco, etc.).
    """
    try:
        store = get_vector_store()
        llm = get_llm()
    except Exception as exc:
        print(f"Erro ao inicializar a busca: {exc}")
        return None

    def build_inputs(pergunta: str) -> dict:
        results = store.similarity_search_with_score(pergunta, k=TOP_K)
        contexto = "\n\n".join(doc.page_content for doc, _score in results)
        return {"contexto": contexto, "pergunta": pergunta}

    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = RunnableLambda(build_inputs) | prompt | llm | StrOutputParser()

    if question is not None:
        return chain.invoke(question)
    return chain
