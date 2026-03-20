"""反馈模块的请求与响应数据模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    """创建反馈请求模型。"""

    user_id: int
    type: str
    content: str
    contact: str | None = None


class FeedbackResponse(BaseModel):
    """反馈响应模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: str
    content: str
    contact: str | None = None
    created_at: datetime
