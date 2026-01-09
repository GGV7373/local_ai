"""
Transcript Export Module

Handles exporting conversations to downloadable text files.
"""

import os
from datetime import datetime
from typing import List, Optional
import json


def format_transcript(
    messages: List[dict],
    company_name: str = "AI Assistant",
    assistant_name: str = "Nora",
    session_id: str = "",
    include_timestamps: bool = True
) -> str:
    """
    Format conversation messages as a readable transcript.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        company_name: Company name for header
        assistant_name: Assistant name
        session_id: Session identifier
        include_timestamps: Whether to include timestamps
    
    Returns:
        Formatted transcript as string
    """
    lines = []
    
    # Header
    lines.append("=" * 60)
    lines.append(f"  {company_name} - Conversation Transcript")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Session ID: {session_id}")
    lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("")
    
    # Messages
    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("created_at", "")
        
        # Format role name
        if role == "user":
            speaker = "You"
        elif role == "assistant":
            speaker = assistant_name
        else:
            speaker = role.capitalize()
        
        # Add timestamp if available
        if include_timestamps and timestamp:
            lines.append(f"[{timestamp}]")
        
        lines.append(f"{speaker}:")
        lines.append(content)
        lines.append("")
    
    # Footer
    lines.append("-" * 60)
    lines.append(f"End of transcript - {len(messages)} messages")
    lines.append("")
    
    return "\n".join(lines)


def format_notes(
    messages: List[dict],
    title: str = "Meeting Notes"
) -> str:
    """
    Format conversation as condensed notes.
    
    Args:
        messages: List of message dicts
        title: Title for the notes
    
    Returns:
        Formatted notes as string
    """
    lines = []
    
    # Header
    lines.append(f"# {title}")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    
    # Extract key points (questions and responses)
    lines.append("## Key Points")
    lines.append("")
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "user":
            # User questions as bullet points
            lines.append(f"**Q:** {content}")
        elif role == "assistant":
            # AI responses indented
            lines.append(f"**A:** {content}")
        
        lines.append("")
    
    return "\n".join(lines)


def save_transcript(
    messages: List[dict],
    output_dir: str,
    session_id: str,
    format: str = "txt"
) -> str:
    """
    Save transcript to file.
    
    Args:
        messages: List of messages
        output_dir: Directory to save to
        session_id: Session ID for filename
        format: Output format ('txt' or 'json')
    
    Returns:
        Path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == "json":
        filename = f"transcript_{session_id}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": session_id,
                "exported_at": datetime.now().isoformat(),
                "messages": messages
            }, f, indent=2, ensure_ascii=False)
    else:
        filename = f"transcript_{session_id}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        transcript = format_transcript(messages, session_id=session_id)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(transcript)
    
    return filepath
