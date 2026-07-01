"""
文档解析工具
支持 PDF, DOCX, Markdown, TXT 文件解析
"""
import aiofiles
from pathlib import Path
from typing import Optional
import pymupdf  # PyMuPDF
from docx import Document
import markdownify
import mammoth


async def extract_text_from_file(
    file_path: str,
    mime_type: Optional[str] = None,
) -> str:
    """
    从文件中提取文本

    Args:
        file_path: 文件路径
        mime_type: MIME 类型（可选）

    Returns:
        提取的文本内容
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 如果没有提供 MIME 类型，根据文件扩展名推断
    if not mime_type:
        mime_type = _guess_mime_type(path)

    # PDF
    if "pdf" in mime_type.lower():
        return await _extract_pdf(file_path)

    # DOCX
    if "wordprocessingml" in mime_type.lower() or "msword" in mime_type.lower() or path.suffix.lower() == ".docx":
        return await _extract_docx(file_path)

    # Markdown
    if "markdown" in mime_type.lower() or path.suffix.lower() in [".md", ".markdown"]:
        return await _extract_markdown(file_path)

    # TXT
    if "text" in mime_type.lower() or path.suffix.lower() == ".txt":
        return await _extract_text(file_path)

    raise ValueError(f"Unsupported file type: {mime_type}")


def _guess_mime_type(path: Path) -> str:
    """根据文件扩展名推断 MIME 类型"""
    ext = path.suffix.lower()

    mime_map = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
    }

    return mime_map.get(ext, "application/octet-stream")


async def _extract_pdf(file_path: str) -> str:
    """从 PDF 提取文本"""
    doc = pymupdf.open(file_path)
    text_parts = []

    for page in doc:
        text_parts.append(page.get_text())

    doc.close()
    return "\n\n".join(text_parts)


async def _extract_docx(file_path: str) -> str:
    """从 DOCX 提取文本"""
    # 使用 mammoth 提取原始文本
    with open(file_path, "rb") as docx_file:
        result = mammoth.extract_raw_text(docx_file)
        return result.value


async def _extract_markdown(file_path: str) -> str:
    """从 Markdown 提取文本（转换为纯文本）"""
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        content = await f.read()

    # 使用 markdownify 将 markdown 转换为纯文本
    # 或者直接返回 markdown 内容
    return content


async def _extract_text(file_path: str) -> str:
    """从 TXT 提取文本"""
    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
        return await f.read()


async def parse_multipart_form(
    files: list,
    form_data: dict,
) -> dict:
    """
    解析 multipart 表单数据

    Args:
        files: 文件列表
        form_data: 表单数据字典

    Returns:
        解析后的数据字典
    """
    result = {
        "q": form_data.get("q", ""),
        "chatId": form_data.get("chatId"),
        "files": [],
    }

    upload_dir = Path.cwd() / "storage" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        filename = file.filename
        content_type = file.content_type

        # 保存文件
        file_path = upload_dir / f"{int(asyncio.get_event_loop().time() * 1000)}-{filename}"

        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        result["files"].append({
            "path": str(file_path),
            "filename": filename,
            "mimeType": content_type,
        })

    return result
