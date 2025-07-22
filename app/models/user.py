"""
Merculy Backend - User Models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BiasType(str, Enum):
    ESQUERDA = "esquerda"
    CENTRO = "centro"
    DIREITA = "direita"

class NewsletterFormat(str, Enum):
    UNICA = "unica"
    POR_ASSUNTO = "por_assunto"

class UserPreferences(BaseModel):
    topics: List[str] = Field(default_factory=list)
    custom_topics: List[str] = Field(default_factory=list)
    newsletter_format: NewsletterFormat = NewsletterFormat.UNICA
    frequency_days: List[str] = Field(default=["monday", "wednesday", "friday"])
    delivery_hour: int = Field(default=8, ge=0, le=23)
    delivery_timezone: str = Field(default="America/Sao_Paulo")

class User(BaseModel):
    id: Optional[str] = None
    user_id: str  # Azure AD B2C sub claim
    email: EmailStr
    name: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    roles: List[str] = Field(default_factory=lambda: ["user"])
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserUpdate(BaseModel):
    name: Optional[str] = None
    preferences: Optional[UserPreferences] = None

class Article(BaseModel):
    title: str
    url: str
    excerpt: str
    content: Optional[str] = None
    source: str
    published_at: datetime
    topic: str
    summary: Optional[str] = None
    bias: Optional[BiasType] = None
    confidence_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)

class Newsletter(BaseModel):
    id: Optional[str] = None
    user_id: str
    date: datetime
    format: NewsletterFormat
    articles: List[Article]
    html_content: str
    sent_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class NewsletterRequest(BaseModel):
    test_mode: bool = False
    immediate_send: bool = False
