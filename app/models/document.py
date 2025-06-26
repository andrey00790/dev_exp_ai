"""
Document Model for document storage and indexing
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Document(Base):
    """Document model for content storage"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, index=True)  # confluence, gitlab, jira, etc.
    source_id = Column(String(255), nullable=True, index=True)
    document_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, title: str, content: str, source: str, 
                 source_id: str = None, metadata: dict = None):
        self.title = title
        self.content = content
        self.source = source
        self.source_id = source_id
        self.document_metadata = metadata or {} 