from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

# 환경에 따라 .env 파일 로드
if os.getenv("ENV", "development") == "development":
    load_dotenv()

PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_ENV = os.environ["PINECONE_ENV"]
INDEX_NAME = "hihello-db-index"

# Pinecone 인스턴스 생성 및 초기화
pinecone_instance = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)

# SentenceTransformer 모델 초기화
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str):
    """문장을 임베딩 벡터로 변환"""
    return model.encode(text)

# Pinecone 인덱스 확인 및 생성
if INDEX_NAME not in pinecone_instance.list_indexes().names():
    pinecone_instance.create_index(
        name=INDEX_NAME,
        dimension=384,  # all-MiniLM-L6-v2의 출력 벡터 크기
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
else:
    print(f"Index '{INDEX_NAME}' already exists.")

# Pinecone 인덱스 객체 가져오기
pc_index = pinecone_instance.Index(name=INDEX_NAME)  # 'Index' 메서드 사용

# Pinecone에 데이터 업로드 함수
def upload_to_pinecone(contents, metadatas, embeddings):
    """
    Pinecone에 데이터를 업로드합니다.
    :param contents: 업로드할 문서 본문
    :param metadatas: 문서 메타데이터
    :param embeddings: 벡터 임베딩
    """
    # 메타데이터와 임베딩을 결합하여 벡터 생성
    vectors = [
        {
            "id": metadatas[i]["id"],  # 메타데이터에서 ID 가져오기
            "values": embeddings[i],  # 임베딩 데이터 추가
            "metadata": {
                **metadatas[i],  # 기존 메타데이터 포함
                "content": contents[i]  # content 필드 추가
            },
        }
        for i in range(len(metadatas))
    ]

    # Pinecone 업로드
    pc_index.upsert(vectors=vectors)
    print(f"Index '{INDEX_NAME}' upload complete.")

# Pinecone 데이터 삭제 함수
def delete_from_pinecone(ids):
    """
    Pinecone에서 데이터를 삭제합니다.
    :param ids: 삭제할 데이터의 ID 리스트
    """
    pc_index.delete(ids=ids)
    print(f"Deleted IDs from '{INDEX_NAME}': {ids}")