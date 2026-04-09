import os
from pathlib import Path
from dotenv import load_dotenv
import aisuite as ai
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

os.environ["HUGGINGFACE_HUB_TOKEN"] = os.getenv("HUGGINGFACE_HUB_TOKEN", "")

api_key = os.getenv('MISTRAL_API_KEY')
if api_key is None:
    raise ValueError("MISTRAL_API_KEY environment variable is not set. Please set it before running.")

provider = "mistral"
model = "ministral-8b-latest"


# ── CoT Pipeline 函式 ────────────────────────────────
# Goal : 生成澎湖旅遊計劃

def user_demand_analysis(provider=provider, model=model,
                         prompt="我沒有特定的需求",
                         system="請列出此使用者所有的需求，請勿想像"):
    client = ai.Client()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(model=f"{provider}:{model}", messages=messages)
    return response.choices[0].message.content


def travel_planner(provider=provider, model=model,
                   prompt="我對澎湖旅遊有興趣，請推薦我一個三天兩夜的澎湖行程",
                   system="生成一個台灣澎湖的旅遊計劃。用純文字加表情符號呈現，不使用任何 markdown 語法（不用 ##、**、--- 等）。行程每天條列簡短。最後加上 [NOTES] 標記，後面接注意事項與住宿建議。"):
    client = ai.Client()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(model=f"{provider}:{model}", messages=messages)
    return response.choices[0].message.content


def critical_reviewer(provider=provider, model=model,
                      prompt="此規劃有問題",
                      system="你是一位嚴謹的旅遊評論家。請列出此規劃不合理的地方（至少三個），並給予原因。\n此外，請特別檢查：\n1. 是否出現「套裝行程」、「業者名稱」、「定價/售價」等生硬的商業字眼？如果有，請指出並要求修正為更自然的在地描述。\n2. 行程是否過於擁擠或地理位置不連貫？"):
    client = ai.Client()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(model=f"{provider}:{model}", messages=messages)
    return response.choices[0].message.content


def travel_replanner(provider=provider, model=model,
                     prompt="不需要修正",
                     system="依據要求進行修正。直接輸出修正後的內容，不要說明修正了什麼。用純文字加表情符號，不使用 markdown。行程結束後加上 [NOTES] 標記，後面接注意事項與住宿建議。"):
    client = ai.Client()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(model=f"{provider}:{model}", messages=messages)
    return response.choices[0].message.content


# ── RAG ─────────────────────────────────────────────
# Note : 約 2 分鐘

class EmbeddingGemmaEmbeddings(HuggingFaceEmbeddings):
    def __init__(self, **kwargs):
        super().__init__(
            model_name="google/embeddinggemma-300m",
            encode_kwargs={"normalize_embeddings": True},
            **kwargs
        )

    def embed_documents(self, texts):
        # 文件向量：title 可用 "none"，或自行帶入檔名/章節標題以微幅加分
        texts = [f'title: none | text: {t}' for t in texts]
        return super().embed_documents(texts)

    def embed_query(self, text):
        # 查詢向量：官方建議的 Retrieval-Query 前綴
        return super().embed_query(f'task: search result | query: {text}')


_FAISS_PATH = Path(__file__).parent.parent / "rag" / "faiss_db"

embedding_model = EmbeddingGemmaEmbeddings()
vectorstore = FAISS.load_local(
    str(_FAISS_PATH),
    embeddings=embedding_model,
    allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 8})


def chat_with_schedule_rag(provider=provider, model=model, user_input="無特定需求"):
    # 取回相關資料
    docs = retriever.invoke(user_input)
    retrieved_chunks = "\n\n".join([doc.page_content for doc in docs])

    prompt_template = """
    你是一位在地的澎湖生活專家，請根據下列提供的活動資訊：
    {retrieved_chunks}

    針對使用者的需求「{question}」，提供最適合的在地行程建議。

    注意事項：
    1. 請以「在地好友推薦」的語氣回答，避免使用「套裝行程」、「定價」、「售價」或「業者名稱」等字眼。
    2. 將活動內容轉換為自然的描述，例如「推薦去藍洞巡航」而不是「藍洞巡航+七美機車套裝」。
    3. 保留重要的時間限制或出發建議（例如：建議早上 08:30 出發），但不要提到這是哪個業者的規定。
    4. 除非使用者詢問，否則不要主動提及價格。
    """
    # 將自定 prompt 套入格式
    final_prompt = prompt_template.format(retrieved_chunks=retrieved_chunks, question=user_input)

    # 用 AI Suite 呼叫語言模型
    client = ai.Client()
    response = client.chat.completions.create(
        model=f"{provider}:{model}",
        messages=[
            {"role": "system", "content": "你是一位熱愛澎湖的在地領路人，擅長將各種在地活動自然地推薦給朋友。"},
            {"role": "user", "content": final_prompt},
        ]
    )
    return response.choices[0].message.content


# ── 對外入口 ─────────────────────────────────────────

def rag_smart_reply(user_text: str) -> str:
    user_demand = user_demand_analysis(prompt=user_text)
    rag_result = chat_with_schedule_rag(user_input="以下是我的需求：" + user_demand)
    planner = travel_planner(
        prompt=user_demand + "。另外，在地好友也給了一些活動建議，請將這些活動自然地規劃進這幾天的行程中，使其看起來像是一場私人的深度旅遊：\n" + rag_result
    )
    reviewer = critical_reviewer(prompt=planner)
    final = travel_replanner(prompt=reviewer)
    return final
