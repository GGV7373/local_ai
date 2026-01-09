"""
Database Models and Connection

Handles conversation memory storage using PostgreSQL.
"""

import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.future import select

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://nora:nora_password@localhost:5432/nora_db"
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class User(Base):
    """User/Client model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to conversations
    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    """Conversation session model."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    """Individual message in a conversation."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    conversation = relationship("Conversation", back_populates="messages")


class MemoryStore:
    """
    Handles conversation memory operations.
    
    Provides methods to store and retrieve conversation history
    for context-aware AI responses.
    """
    
    @staticmethod
    async def init_db():
        """Initialize database tables."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @staticmethod
    async def get_or_create_user(client_id: str, name: Optional[str] = None) -> User:
        """Get existing user or create new one."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.client_id == client_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(client_id=client_id, name=name)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            else:
                user.last_active = datetime.utcnow()
                await session.commit()
            
            return user
    
    @staticmethod
    async def create_conversation(client_id: str, session_id: str, title: Optional[str] = None) -> Conversation:
        """Create a new conversation session."""
        async with async_session() as session:
            # Get or create user
            result = await session.execute(
                select(User).where(User.client_id == client_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(client_id=client_id)
                session.add(user)
                await session.flush()
            
            conversation = Conversation(
                user_id=user.id,
                session_id=session_id,
                title=title
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            
            return conversation
    
    @staticmethod
    async def get_conversation(session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID."""
        async with async_session() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def add_message(session_id: str, role: str, content: str) -> Message:
        """Add a message to a conversation."""
        async with async_session() as session:
            # Get conversation
            result = await session.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                raise ValueError(f"Conversation {session_id} not found")
            
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=content
            )
            session.add(message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(message)
            
            return message
    
    @staticmethod
    async def get_conversation_history(session_id: str, limit: int = 20) -> List[dict]:
        """Get recent messages from a conversation."""
        async with async_session() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                return []
            
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()
            
            # Return in chronological order
            return [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(messages)
            ]
    
    @staticmethod
    async def get_user_conversations(client_id: str, limit: int = 50) -> List[dict]:
        """Get all conversations for a user."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.client_id == client_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return []
            
            result = await session.execute(
                select(Conversation)
                .where(Conversation.user_id == user.id)
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
            )
            conversations = result.scalars().all()
            
            return [
                {
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat()
                }
                for conv in conversations
            ]
