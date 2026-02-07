#!/usr/bin/env python3
"""
API 服务 - 雪中悍刀行专家级问答
使用 FastAPI 提供 REST API 接口
"""

import sys
import os
from pathlib import Path
from typing import Optional

# 添加 src 到路径
sys.path.append(str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入专家系统
try:
    from expert_system_v2 import ExpertSystemV2
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在正确的目录运行")
    sys.exit(1)

# 创建 FastAPI 应用
app = FastAPI(
    title="雪中悍刀行 - 专家级问答 API",
    description="基于全文深度分析的文学评论级问答系统",
    version="2.0.0"
)

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量 - 专家系统
system = None

@app.on_event("startup")
async def startup_event():
    """启动时加载专家系统"""
    global system
    print("🚀 正在加载专家系统...")
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        system = ExpertSystemV2(data_dir="data", api_key=api_key)
        print("✅ 专家系统加载完成！")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        raise

# 请求模型
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    temperature: Optional[float] = 0.7

# 响应模型
class QueryResponse(BaseModel):
    success: bool
    query: str
    answer: Optional[str] = None
    context: Optional[str] = None
    usage: Optional[dict] = None
    error: Optional[str] = None

@app.get("/")
async def root():
    """根路径 - 服务状态"""
    return {
        "status": "running",
        "service": "雪中悍刀行专家级问答 API",
        "version": "2.0.0",
        "endpoints": {
            "POST /query": "提交问题获取回答",
            "GET /search": "检索相关段落",
            "GET /health": "健康检查"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "system_loaded": system is not None
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    提交问题，获取专家级回答
    
    - **query**: 问题文本
    - **top_k**: 检索段落数量（默认5）
    - **temperature**: 生成温度（默认0.7）
    """
    if system is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        result = system.answer(request.query, temperature=request.temperature)
        
        # 获取上下文
        context = system.get_context(request.query, top_k=request.top_k)
        
        return QueryResponse(
            success=result.get("success", False),
            query=request.query,
            answer=result.get("answer"),
            context=context,
            usage=result.get("usage"),
            error=result.get("error")
        )
    except Exception as e:
        return QueryResponse(
            success=False,
            query=request.query,
            error=str(e)
        )

@app.get("/search")
async def search(q: str, top_k: Optional[int] = 5):
    """
    检索相关段落
    
    - **q**: 查询关键词
    - **top_k**: 返回结果数量
    """
    if system is None:
        raise HTTPException(status_code=503, detail="系统未初始化")
    
    try:
        results = system.retrieve(q, top_k=top_k)
        return {
            "query": q,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def stats():
    """获取系统统计信息"""
    return {
        "paragraphs": 12378,
        "entities": 10820,
        "events": 2236,
        "characters": 14
    }

if __name__ == "__main__":
    # 本地运行
    uvicorn.run(app, host="0.0.0.0", port=8000)
