"""Build Notion blocks from RecallItem content.

Converts plaintext content into Notion block structures:
- headings (#, ##)
- bullets (-, *)
- code fences (```)
- quote blocks (>)
- paragraphs
"""

import re
from typing import List, Dict

def _text_block(text: str) -> Dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}


def build_blocks(content: str) -> List[Dict]:
    blocks = []
    lines = content.splitlines()
    i = 0
    in_code = False
    code_buf = []

    while i < len(lines):
        line = lines[i].rstrip()
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                # end code block
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {"text": [{"type": "text", "text": {"content": "\n".join(code_buf)}}]},
                })
                in_code = False
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # headings
        if re.match(r"^#{1,6}\s+", line):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            blocks.append({
                "object": "block",
                "type": "heading_{}".format(1 if level == 1 else (2 if level == 2 else 3)),
                f"heading_{1 if level == 1 else (2 if level == 2 else 3)}": {"rich_text": [{"type": "text", "text": {"content": text}}]}
            })
            i += 1
            continue

        # quote
        if line.strip().startswith('>'):
            text = line.lstrip('>').strip()
            blocks.append({"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": text}}]}})
            i += 1
            continue

        # bullets
        if re.match(r"^[\-\*]\s+", line):
            text = re.sub(r"^[\-\*]\s+", '', line).strip()
            blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}})
            i += 1
            continue

        # paragraph (merge consecutive non-empty lines)
        if line.strip() == '':
            i += 1
            continue

        para_lines = [line]
        j = i + 1
        while j < len(lines) and lines[j].strip() != '' and not re.match(r"^(#{1,6}|\-|\*|>|```)", lines[j]):
            para_lines.append(lines[j])
            j += 1
        blocks.append(_text_block(' '.join(para_lines).strip()))
        i = j

    return blocks
"""Notion block building utilities.

Provides utilities for constructing Notion blocks from content.
"""

from typing import Any, Dict, List


class BlockBuilder:
    """Builder for constructing Notion blocks.
    
    Converts various content types into Notion block structures.
    """
    
    @staticmethod
    def build_paragraph(text: str) -> Dict[str, Any]:
        """Build a paragraph block.
        
        Args:
            text: Paragraph text.
            
        Returns:
            Notion paragraph block structure.
        """
        # TODO: Implement paragraph block building
        # - Create paragraph block structure
        # - Handle text formatting
        # - Return block dict
        raise NotImplementedError("Paragraph block building not yet implemented")
    
    @staticmethod
    def build_heading(text: str, level: int = 1) -> Dict[str, Any]:
        """Build a heading block.
        
        Args:
            text: Heading text.
            level: Heading level (1, 2, or 3).
            
        Returns:
            Notion heading block structure.
        """
        # TODO: Implement heading block building
        # - Validate heading level
        # - Create heading block structure
        # - Return block dict
        raise NotImplementedError("Heading block building not yet implemented")
    
    @staticmethod
    def build_bulleted_list(items: List[str]) -> List[Dict[str, Any]]:
        """Build bulleted list blocks.
        
        Args:
            items: List items.
            
        Returns:
            List of Notion bulleted list block structures.
        """
        # TODO: Implement bulleted list building
        # - Create list item blocks
        # - Handle nesting
        # - Return list of blocks
        raise NotImplementedError("Bulleted list building not yet implemented")
    
    @staticmethod
    def build_blocks_from_content(content: str) -> List[Dict[str, Any]]:
        """Build blocks from content string.
        
        Args:
            content: Content string (may contain markdown).
            
        Returns:
            List of Notion blocks.
        """
        # TODO: Implement content parsing
        # - Parse content structure
        # - Build appropriate blocks
        # - Handle formatting
        # - Return list of blocks
        raise NotImplementedError("Content to blocks conversion not yet implemented")
