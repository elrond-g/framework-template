"""LLM 专用日志模块。

提供两个独立日志文件：
- llm-digest.log  — 摘要日志（一行一条，管道符分隔）
- llm-describe.log — 详情日志（JSONL 格式，含完整请求/响应内容）
"""

import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from config.settings import settings

# ── 日志目录 ──────────────────────────────────────────────
_LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    settings.log_dir,
)
os.makedirs(_LOG_DIR, exist_ok=True)

_DATE_FMT = "%Y-%m-%d %H:%M:%S.%f"


def _make_file_logger(name: str, filename: str) -> logging.Logger:
    """创建只写文件的 logger（不输出到控制台）。"""
    _logger = logging.getLogger(name)
    if _logger.handlers:
        return _logger
    _logger.setLevel(logging.INFO)
    _logger.propagate = False  # 不向上层传播，避免重复输出

    handler = RotatingFileHandler(
        os.path.join(_LOG_DIR, filename),
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    # 不加格式前缀，由调用方自行拼接内容
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
    return _logger


_digest_logger = _make_file_logger("llm.digest", "llm-digest.log")
_describe_logger = _make_file_logger("llm.describe", "llm-describe.log")


def log_llm_request(
    *,
    request_id: str,
    start_time: datetime,
    end_time: datetime,
    input_length: int,
    output_length: int,
    ttft_ms: float,
    topt: float,
    success: bool,
    error_reason: Optional[str] = None,
    request_content: Optional[list[dict]] = None,
    response_content: Optional[str] = None,
) -> None:
    """同时写入摘要日志和详情日志。

    Parameters
    ----------
    request_id : 请求唯一标识
    start_time : 请求开始时间
    end_time : 请求结束时间
    input_length : 输入内容字符长度
    output_length : 输出内容字符长度
    ttft_ms : Time To First Token（毫秒，非流式 = 总耗时）
    topt : 输出吞吐量（chars/s）
    success : 是否成功
    error_reason : 失败原因（成功时为 None）
    request_content : 完整请求 messages（仅写入 describe）
    response_content : 完整返回内容（仅写入 describe）
    """
    log_time = datetime.now().strftime(_DATE_FMT)[:-3]  # 精确到毫秒
    start_str = start_time.strftime(_DATE_FMT)[:-3]
    end_str = end_time.strftime(_DATE_FMT)[:-3]

    # ── digest: 管道符分隔的一行摘要 ──
    digest_parts = [
        log_time,
        request_id,
        start_str,
        end_str,
        str(input_length),
        str(output_length),
        f"{ttft_ms:.1f}ms",
        f"{topt:.1f}chars/s",
        "SUCCESS" if success else "FAILED",
        error_reason or "",
    ]
    _digest_logger.info(" | ".join(digest_parts))

    # ── describe: JSONL 格式的完整记录 ──
    describe_record = {
        "log_time": log_time,
        "request_id": request_id,
        "start_time": start_str,
        "end_time": end_str,
        "input_length": input_length,
        "output_length": output_length,
        "ttft_ms": round(ttft_ms, 1),
        "topt_chars_per_s": round(topt, 1),
        "success": success,
        "error_reason": error_reason,
        "request_content": request_content,
        "response_content": response_content,
    }
    _describe_logger.info(json.dumps(describe_record, ensure_ascii=False))
