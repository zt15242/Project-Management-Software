import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List

from auth import get_current_active_user
from models import (
    UserResponse, ChatSessionResponse, ChatSessionCreate, ChatSessionUpdate,
    ChatMessage, ChatMessageUpdate
)
from api.models import ChatCompletionRequest
from services.ai.ai_service import ai_service
from services.ai.skills import get_all_skills
from database import get_database
from bson import ObjectId
from utils import get_beijing_time

router = APIRouter(prefix="/api/landppt", tags=["LandPPT AI助手"])

# ==========================================
# 会话管理 API (迁移自 ai_assistant.py)
# ==========================================

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    session: ChatSessionCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    db = Depends(get_database)
):
    new_session = {
        "user_id": current_user.id,
        "project_id": session.project_id,
        "title": session.title,
        "created_at": get_beijing_time(),
        "updated_at": get_beijing_time()
    }
    result = await db.ai_sessions.insert_one(new_session)
    return {**new_session, "id": str(result.inserted_id)}

@router.get("/projects/{project_id}/sessions", response_model=List[ChatSessionResponse])
async def get_project_sessions(
    project_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db = Depends(get_database)
):
    cursor = db.ai_sessions.find({"project_id": project_id, "user_id": current_user.id}).sort("updated_at", -1)
    sessions = await cursor.to_list(length=100)
    return [{**s, "id": str(s["_id"])} for s in sessions]

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db = Depends(get_database)
):
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
        
    session = await db.ai_sessions.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    cursor = db.ai_messages.find({"session_id": session_id}).sort("created_at", 1)
    messages = await cursor.to_list(length=1000)
    
    # 转换逻辑
    result = []
    for msg in messages:
        msg["id"] = str(msg.pop("_id"))
        result.append(msg)
    return result

@router.patch("/messages/{message_id}", response_model=ChatMessage)
async def update_message(
    message_id: str,
    update: ChatMessageUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db = Depends(get_database)
):
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID")
        
    message = await db.ai_messages.find_one({"_id": ObjectId(message_id)})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
        
    session = await db.ai_sessions.find_one({"_id": ObjectId(message["session_id"])})
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db.ai_messages.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"content": update.content, "updated_at": get_beijing_time()}}
    )
    
    updated_msg = await db.ai_messages.find_one({"_id": ObjectId(message_id)})
    updated_msg["id"] = str(updated_msg.pop("_id"))
    return updated_msg

@router.delete("/messages/{message_id}")
async def delete_message_and_after(
    message_id: str,
    include_self: bool = True,
    current_user: UserResponse = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Delete a message and all messages that came after it in the same session.
    Useful for 'Edit & Regenerate' functionality.
    """
    if not ObjectId.is_valid(message_id):
        raise HTTPException(status_code=400, detail="Invalid message ID")
        
    message = await db.ai_messages.find_one({"_id": ObjectId(message_id)})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
        
    session_id = message["session_id"]
    session = await db.ai_sessions.find_one({"_id": ObjectId(session_id)})
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Find all messages in this session created after this one
    query = {
        "session_id": session_id,
        "created_at": {"$gt": message["created_at"]}
    }
    
    if include_self:
        await db.ai_messages.delete_one({"_id": ObjectId(message_id)})
        
    await db.ai_messages.delete_many(query)
    
    return {"status": "success", "message": "Messages deleted"}

@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: str,
    update: ChatSessionUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db = Depends(get_database)
):
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
        
    session = await db.ai_sessions.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db.ai_sessions.update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"title": update.title, "updated_at": get_beijing_time()}}
    )
    
    updated_session = await db.ai_sessions.find_one({"_id": ObjectId(session_id)})
    return {**updated_session, "id": str(updated_session["_id"])}

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db = Depends(get_database)
):
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
        
    session = await db.ai_sessions.find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # 删除会话
    await db.ai_sessions.delete_one({"_id": ObjectId(session_id)})
    # 删除会话下的消息
    await db.ai_messages.delete_many({"session_id": session_id})
    
    return {"status": "success", "message": "Session deleted"}


@router.post("/chat")
async def chat_with_assistant(
    request: ChatCompletionRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Standard chat interface with AI assistant.
    Automatically uses the active AI configuration from database.
    """
    try:
        # We can detect context layer here or pass it from frontend
        context = {"user_id": current_user.id, "layer": "general"}
        
        # If user mentions research or searching, we can hint the layer
        last_msg = request.messages[-1].content.lower()
        if any(w in last_msg for w in ["调研", "搜索", "研究", "research", "search"]):
            context["layer"] = "research"
        elif any(w in last_msg for w in ["大纲", "框架", "结构", "outline", "structure"]):
            context["layer"] = "outline"

        response_content = await ai_service.chat(request, context=context)
        return {"content": response_content}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream-chat")
async def stream_chat_with_assistant(
    request: ChatCompletionRequest,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Streaming chat interface for better UX.
    """
    async def event_generator():
        try:
            context = {"user_id": current_user.id, "layer": "general"}
            
            # Simple intent detection
            last_msg = request.messages[-1].content.lower()
            if any(w in last_msg for w in ["调研", "搜索", "研究"]):
                context["layer"] = "research"
            
            # 获取数据库实例
            from database import get_database
            from bson import ObjectId
            from utils import get_beijing_time
            db = get_database()
            
            # --- 处理引用资源 (移植自 ai_assistant.py 的逻辑) ---
            resource_context = ""
            if request.resources:
                context_parts = []
                
                # 1. 知识库文档
                if request.resources.get("knowledge"):
                    context_parts.append("## 相关知识库文档\n")
                    import io
                    import os
                    from utils.oss_utils import download_file_from_oss
                    from routers.knowledge import extract_text_content, KnowledgeFileType
                    
                    for doc_item in request.resources["knowledge"]:
                        # 兼容不同格式的ID字段
                        doc_id = doc_item.get("id") or doc_item.get("_id")
                        title = doc_item.get("title", "未命名文档")
                        file_type = doc_item.get("file_type", "")
                        
                        context_parts.append(f"### {title} (类型: {file_type})\n")
                        
                        # 图片特殊处理
                        if file_type == "image":
                            context_parts.append("(这是一个图片文件，目前暂不支持自动提取图片中的文字内容。请提示用户如果图片包含重要文字，请手动描述或使用OCR工具提取后发送。)\n\n")
                            continue
                        
                        content = ""
                        initial_content = doc_item.get("content", "")
                        
                        # 判断是否需要重新提取
                        needs_reextract = not initial_content or "提取失败" in initial_content or "Package not found" in initial_content
                        
                        # 尝试从数据库获取或重新提取
                        if doc_id and ObjectId.is_valid(str(doc_id)):
                            db_doc = await db.knowledge.find_one({"_id": ObjectId(str(doc_id))})
                            if db_doc:
                                # 二次检查文件类型
                                db_file_type = db_doc.get("file_type")
                                if db_file_type == "image":
                                    context_parts.append("(这是一个图片文件，目前暂不支持自动提取图片中的文字内容。)\n\n")
                                    continue
                                    
                                existing_content = db_doc.get("content", "")
                                if existing_content and "提取失败" not in existing_content:
                                    content = existing_content
                                else:
                                    # 尝试实时提取
                                    try:
                                        storage_type = db_doc.get("storage_type", "local")
                                        file_path = db_doc.get("file_path")
                                        
                                        if storage_type == "oss":
                                            oss_key = db_doc.get("oss_key")
                                            if oss_key:
                                                file_bytes = await download_file_from_oss(oss_key)
                                                if db_file_type in [KnowledgeFileType.WORD, KnowledgeFileType.EXCEL, KnowledgeFileType.PPT]:
                                                    if not file_bytes.startswith(b'PK\x03\x04'):
                                                        print(f"[LandPPT-Chat] 警告: 文件签名校验失败")
                                                content = await extract_text_content(io.BytesIO(file_bytes), KnowledgeFileType(db_file_type))
                                        elif storage_type == "local" and file_path and os.path.exists(file_path):
                                            content = await extract_text_content(file_path, KnowledgeFileType(db_file_type))
                                        
                                        if content:
                                            # 更新回数据库
                                            await db.knowledge.update_one(
                                                {"_id": ObjectId(str(doc_id))},
                                                {"$set": {"content": content}}
                                            )
                                    except Exception as e:
                                        print(f"[LandPPT-Chat] 提取失败: {e}")

                        # 兜底使用前端传来的内容
                        if not content:
                            if initial_content and "提取失败" not in initial_content:
                                content = initial_content
                        
                        if content:
                            context_parts.append(f"{content[:5000]}\n\n")
                        else:
                            context_parts.append(f"(该文档({file_type})文字内容提取失败或为空。)\n\n")

                # 2. 会议纪要
                if request.resources.get("meetings"):
                    context_parts.append("## 相关会议纪要\n")
                    for meeting in request.resources["meetings"]:
                        context_parts.append(f"### {meeting.get('title', '会议')}\n")
                        if meeting.get("summary"):
                            # 尝试解析 summary 字段（可能是 JSON 字符串）
                            try:
                                summary_text = meeting["summary"]
                                if isinstance(summary_text, str) and (summary_text.startswith('{') or summary_text.startswith('[')):
                                     data = json.loads(summary_text)
                                     summary_text = data.get('summary', str(data))
                                context_parts.append(f"{summary_text}\n\n")
                            except:
                                context_parts.append(f"{meeting['summary']}\n\n")

                resource_context = "".join(context_parts)

            # 将资源上下文注入到消息列表的最前面 (System Message)
            if resource_context:
                from api.models import ChatMessage
                # 注入额外的一条 System Message 告知 AI 此时有参考资料
                resource_msg = ChatMessage(
                    role="system",
                    content=f"以下是用户引用的参考资料（文档/会议纪要），请根据这些资料回答用户的问题：\n\n{resource_context}"
                )
                # 插入到倒数第二个位置（如果是最后一个是User，那就在User之前；或者直接插在开头）
                # 为了稳妥，插在 request.messages 的开头，但在 System Prompt 之后
                # 由于 ai_service 会自己构建 System Prompt，我们这里把这个作为第二条 System Message 传入
                request.messages.insert(0, resource_msg)

            
            # 1. 自动保存用户消息
            session_id = request.session_id
            if session_id and ObjectId.is_valid(session_id):
                # 提取最新的用户消息
                user_content = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
                if user_content:
                    await db.ai_messages.insert_one({
                        "session_id": session_id,
                        "role": "user",
                        "content": user_content,
                        "created_at": get_beijing_time()
                    })
                    # 更新会话活跃时间
                    await db.ai_sessions.update_one(
                        {"_id": ObjectId(session_id)},
                        {"$set": {"updated_at": get_beijing_time()}}
                    )

            # --- 流式输送并收集 ---
            full_response = ""
            async for chunk in ai_service.stream_chat(request, context=context):
                if chunk:
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # 2. 保存完完整回复后存入数据库
            if session_id and ObjectId.is_valid(session_id) and full_response:
                await db.ai_messages.insert_one({
                    "session_id": session_id,
                    "role": "assistant",
                    "content": full_response,
                    "created_at": get_beijing_time()
                })
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/skills")
async def list_available_skills(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    List what 'Superpowers' the AI assistant currently has.
    """
    skills = get_all_skills()
    return [
        {"name": s.name, "description": s.description}
        for s in skills
    ]
