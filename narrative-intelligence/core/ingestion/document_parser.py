from typing import List, Optional
from pydantic import BaseModel

class Chunk(BaseModel):
    chunk_id: str
    text: str
    start_offset: int
    end_offset: int
    section_title: Optional[str] = None

class Document(BaseModel):
    document_id: str
    raw_text: str
    chunks: List[Chunk]
    metadata: dict

class DocumentParser:
    """Handles ingestion of raw text into structured Document with chunks."""
    
    def parse_text(self, document_id: str, raw_text: str, metadata: dict = None) -> Document:
        """
        Parses raw text, preserving offsets. 
        In a real implementation, this would handle PDF/DOCX via extensions.
        """
        if metadata is None:
            metadata = {}
            
        # Basic chunking by double newline (paragraphs)
        chunks = []
        start_offset = 0
        paragraphs = raw_text.split('\n\n')
        
        for i, para in enumerate(paragraphs):
            para_clean = para.strip()
            if not para_clean:
                start_offset += len(para) + 2
                continue
                
            end_offset = start_offset + len(para_clean)
            chunks.append(Chunk(
                chunk_id=f"chunk_{i}",
                text=para_clean,
                start_offset=start_offset,
                end_offset=end_offset
            ))
            start_offset += len(para) + 2 # +2 for the \n\n
            
        return Document(
            document_id=document_id,
            raw_text=raw_text,
            chunks=chunks,
            metadata=metadata
        )
