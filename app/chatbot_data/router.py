from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db_connection.rds_connection import get_db
from app.chatbot_data.schema import ChatbotAddRequest, ChatbotUpdateRequest
from app.chatbot_data.model import Chatbot
from app.chatbot_category.model import ChatbotCategory
from app.db_connection.pinecone_connection import upload_to_pinecone, delete_from_pinecone, generate_embedding

router = APIRouter(
    prefix="/api/v1/hr/chatbot",
    tags=["Chatbot"]
)

@router.get("/category/{categorySeq}/data")
def get_chatbot_data_by_category(categorySeq: int, db: Session = Depends(get_db)):
    category = db.query(ChatbotCategory).filter_by(chatbot_category_seq=categorySeq).first()
    if not category:
        raise HTTPException(
            status_code=404,
            detail=f"Chatbot category with ID {categorySeq} not found."
        )
    chatbot_data = db.query(Chatbot).filter_by(chatbot_category_seq=categorySeq).all()
    return {
        "success": True,
        "data": [{"id": data.chatbot_seq, "content": data.chatbot_data} for data in chatbot_data]
    }

@router.post("/category/{categorySeq}/data")
def add_chatbot_data(
        categorySeq: int,
        request_body: ChatbotAddRequest,
        db: Session = Depends(get_db)
):
    try:
        # RDB 작업
        category = db.query(ChatbotCategory).filter_by(chatbot_category_seq=categorySeq).first()
        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Chatbot category with ID {categorySeq} not found."
            )
        new_data = Chatbot(
            chatbot_category_seq=categorySeq,
            chatbot_data=request_body.chatbotData
        )
        db.add(new_data)
        db.flush()

        # 임베딩 생성
        embedding_vector = generate_embedding(request_body.chatbotData)

        # Pinecone 업로드
        upload_to_pinecone(
            contents=[request_body.chatbotData],
            metadatas=[{"id": str(new_data.chatbot_seq)}],
            embeddings=[embedding_vector]  # 생성된 임베딩 전달
        )

        db.commit()
        return {"message": "Chatbot data added successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add chatbot data: {str(e)}"
        )

@router.put("/category/{categorySeq}/data/{chatbotSeq}")
def update_chatbot_data(
        categorySeq: int,
        chatbotSeq: int,
        request_body: ChatbotUpdateRequest,
        db: Session = Depends(get_db)
):
    try:
        # RDB 작업
        category = db.query(ChatbotCategory).filter_by(chatbot_category_seq=categorySeq).first()
        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Chatbot category with ID {categorySeq} not found."
            )
        chatbot_data = db.query(Chatbot).filter_by(chatbot_seq=chatbotSeq, chatbot_category_seq=categorySeq).first()
        if not chatbot_data:
            raise HTTPException(
                status_code=404,
                detail=f"Chatbot data with ID {chatbotSeq} not found in category {categorySeq}."
            )
        chatbot_data.chatbot_data = request_body.chatbotData

        # 임베딩 생성
        embedding_vector = generate_embedding(request_body.chatbotData)

        # Pinecone 업데이트
        upload_to_pinecone(
            contents=[request_body.chatbotData],
            metadatas=[{"id": str(chatbotSeq)}],
            embeddings=[embedding_vector]  # 생성된 임베딩 전달
        )

        db.commit()
        return {"message": "Chatbot data updated successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update chatbot data: {str(e)}"
        )

@router.delete("/category/{categorySeq}/data/{chatbotSeq}")
def delete_chatbot_data(categorySeq: int, chatbotSeq: int, db: Session = Depends(get_db)):
    try:
        # RDB 작업
        category = db.query(ChatbotCategory).filter_by(chatbot_category_seq=categorySeq).first()
        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Chatbot category with ID {categorySeq} not found."
            )
        chatbot_data = db.query(Chatbot).filter_by(chatbot_seq=chatbotSeq, chatbot_category_seq=categorySeq).first()
        if not chatbot_data:
            raise HTTPException(
                status_code=404,
                detail=f"Chatbot data with ID {chatbotSeq} not found in category {categorySeq}."
            )
        db.delete(chatbot_data)

        # Pinecone 삭제
        delete_from_pinecone(ids=[str(chatbotSeq)])

        db.commit()
        return {"message": "Chatbot data deleted successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chatbot data: {str(e)}"
        )