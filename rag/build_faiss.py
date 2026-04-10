"""
FAISS 向量資料庫建立腳本

用途：
    將 rag/source_docs/Panghu_schedule_database.md 向量化，
    建立 FAISS 索引並儲存至 rag/faiss_db/。

使用方式：
    python rag/build_faiss.py

注意：
    - 需要先登入 HuggingFace（huggingface-cli login）
    - 需要有 google/embeddinggemma-300m 模型存取權限
    - 首次執行會下載模型，約需 5-15 分鐘
    - 建立向量庫約需 2-5 分鐘
"""

from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ── 路徑設定 ──────────────────────────────────────────
_ROOT        = Path(__file__).parent.parent
_SOURCE_PATH = _ROOT / "rag" / "source_docs" / "Panghu_schedule_database.md"
_FAISS_PATH  = _ROOT / "rag" / "faiss_db"


# ── Embedding 模型（與 rag_service.py 相同，確保向量空間一致）──
class EmbeddingGemmaEmbeddings(HuggingFaceEmbeddings):
    def __init__(self, **kwargs):
        super().__init__(
            model_name="google/embeddinggemma-300m",
            encode_kwargs={"normalize_embeddings": True},
            **kwargs
        )

    def embed_documents(self, texts):
        # 文件向量：加入 title 前綴
        texts = [f'title: none | text: {t}' for t in texts]
        return super().embed_documents(texts)

    def embed_query(self, text):
        # 查詢向量：官方建議的 Retrieval-Query 前綴
        return super().embed_query(f'task: search result | query: {text}')


def build():
    # ── Step 1：讀取原始文件 ──────────────────────────────
    print(f"📄 讀取文件：{_SOURCE_PATH}")
    if not _SOURCE_PATH.exists():
        raise FileNotFoundError(f"找不到原始文件：{_SOURCE_PATH}")

    loader = TextLoader(str(_SOURCE_PATH), encoding="utf-8")
    docs = loader.load()

    # ── Step 2：依 Markdown 標題切割 ─────────────────────
    print("✂️  切割文件...")
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
    )
    chunks = splitter.split_text(docs[0].page_content)
    print(f"   共切出 {len(chunks)} 個 chunk")

    # ── Step 3：載入 Embedding 模型（約 2 分鐘）─────────
    print("🤖 載入 Embedding 模型（首次需下載，約 5-15 分鐘）...")
    embedding_model = EmbeddingGemmaEmbeddings()

    # ── Step 4：建立 FAISS 向量庫 ────────────────────────
    print("🔨 建立 FAISS 向量庫...")
    vectorstore = FAISS.from_documents(chunks, embedding_model)

    # ── Step 5：儲存 ──────────────────────────────────────
    _FAISS_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(_FAISS_PATH))
    print(f"✅ 完成！已儲存至 {_FAISS_PATH}")


if __name__ == "__main__":
    build()
