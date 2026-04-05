"""
PageLM Python 后端
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
import os
import shutil
import subprocess

from config import config
from api.routes import auth, chat, notes, quiz, podcast, flashcards, files, speaking, slides, lesson_plan, paper, teaching_video, bilibili, transcriber, companion, exam, debate, planner
from utils.auth_db import auth_db


# 创建 FastAPI 应用
app = FastAPI(
    title="PageLM API",
    description="AI-powered learning platform backend",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# 挂载静态文件目录
storage_dir = config.storage_dir
app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

# 注册路由
app.include_router(auth.router, tags=["auth"])
app.include_router(chat.router, tags=["chat"])
app.include_router(notes.router, tags=["notes"])
app.include_router(quiz.router, tags=["quiz"])
app.include_router(podcast.router, tags=["podcast"])
app.include_router(flashcards.router, tags=["flashcards"])
app.include_router(files.router, tags=["files"])
app.include_router(speaking.router, tags=["speaking"])
app.include_router(transcriber.router, tags=["transcriber"])
app.include_router(companion.router, tags=["companion"])
app.include_router(exam.router, tags=["exam"])
app.include_router(debate.router, tags=["debate"])
app.include_router(planner.router, tags=["planner"])
app.include_router(slides.router, tags=["slides"])
app.include_router(lesson_plan.router, tags=["lesson_plan"])
app.include_router(paper.router, tags=["paper"])
app.include_router(teaching_video.router, tags=["teaching_video"])
app.include_router(bilibili.router, tags=["bilibili"])


@app.on_event("startup")
async def startup_bilibili_bridge():
    auth_db.initialize()
    node_path = shutil.which("node")
    if not node_path:
        print("[WARN] Node.js not found, skip starting bilibili MCP bridge")
        return

    backend_dir = Path(__file__).resolve().parent
    bridge_entry = backend_dir / "services" / "bilibiliBridgeServer.js"

    if not bridge_entry.exists():
        print("[WARN] bilibili bridge server file not found, skip startup")
        return

    env = os.environ.copy()
    bridge_port = env.get("BILIBILI_BRIDGE_PORT", "5001")
    env.setdefault("BILIBILI_BRIDGE_URL", f"http://127.0.0.1:{bridge_port}")

    try:
        app.state.bilibili_bridge_proc = subprocess.Popen(
            [node_path, str(bridge_entry)],
            cwd=str(backend_dir),
            env=env,
        )
        print(f"[INFO] bilibili MCP bridge started on port {bridge_port}")
    except Exception as exc:
        print(f"[WARN] failed to start bilibili MCP bridge: {exc}")


@app.on_event("shutdown")
async def shutdown_bilibili_bridge():
    proc = getattr(app.state, "bilibili_bridge_proc", None)
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
        print("[INFO] bilibili MCP bridge stopped")
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "status": "ok",
        "message": "PageLM Python Backend is running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    return {
        "status": "healthy",
        "llm_provider": config.llm_provider,
        "emb_provider": config.emb_provider,
    }


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level="info",
    )
