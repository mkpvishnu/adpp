"""
@ai-metadata {
    "domain": "metadata-parser",
    "description": "Parser for extracting ADP metadata from code files",
    "dependencies": ["schema.py"]
}
"""

import re
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from adp_py.core.schema import ADPSchema, get_schema, ADPMetadata

# Set up logging
logger = logging.getLogger(__name__)

class CodeScope(str, Enum):
    """Scope of the metadata in the code."""
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"


@dataclass
class ParsedFile:
    """Representation of a parsed file with ADP metadata."""
    file_path: str
    metadata_blocks: List[ADPMetadata]
    
    @property
    def has_metadata(self) -> bool:
        """Check if the file has any metadata blocks."""
        return len(self.metadata_blocks) > 0


# Language-specific comment patterns
COMMENT_PATTERNS = {
    "py": {
        "single": r"#\s*@ai-metadata\s*({.*})",  # Single line comment
        "multi_start": r'"""',  # Start of multiline comment
        "multi_end": r'"""',    # End of multiline comment
        "multi_pattern": r'"""(?:\s*\n)?(?:[\s\S]*?)@ai-metadata\s*(\{[\s\S]*?\})',  # Multiline comment with metadata
        "line_comment": r"#"    # Line comment marker
    },
    "js": {
        "single": r"//\s*@ai-metadata\s*({.*})",  # Single line comment
        "multi_start": r"/\*\*",  # Start of multiline comment
        "multi_end": r"\*/",      # End of multiline comment
        "multi_pattern": r"/\*\*[\s\S]*?@ai-metadata\s*({[\s\S]*?})[\s\S]*?\*/",  # Multiline comment with metadata
        "line_comment": r"\*"      # Line comment marker
    },
    "ts": {
        "single": r"//\s*@ai-metadata\s*({.*})",  # Single line comment
        "multi_start": r"/\*\*",  # Start of multiline comment
        "multi_end": r"\*/",      # End of multiline comment
        "multi_pattern": r"/\*\*[\s\S]*?@ai-metadata\s*({[\s\S]*?})[\s\S]*?\*/",  # Multiline comment with metadata
        "line_comment": r"\*"      # Line comment marker
    },
    "java": {
        "single": r"//\s*@ai-metadata\s*({.*})",  # Single line comment
        "multi_start": r"/\*\*",  # Start of multiline comment
        "multi_end": r"\*/",      # End of multiline comment
        "multi_pattern": r"/\*\*[\s\S]*?@ai-metadata\s*({[\s\S]*?})[\s\S]*?\*/",  # Multiline comment with metadata
        "line_comment": r"\*"      # Line comment marker
    },
    "cs": {
        "single": r"//\s*@ai-metadata\s*({.*})",  # Single line comment
        "multi_start": r"/\*\*",  # Start of multiline comment
        "multi_end": r"\*/",      # End of multiline comment
        "multi_pattern": r"/\*\*[\s\S]*?@ai-metadata\s*({[\s\S]*?})[\s\S]*?\*/",  # Multiline comment with metadata
        "line_comment": r"\*"      # Line comment marker
    },
}

# File extension to language mapping
EXTENSION_TO_LANGUAGE = {
    ".py": "py",
    ".js": "js",
    ".jsx": "js",
    ".ts": "ts",
    ".tsx": "ts",
    ".java": "java",
    ".cs": "cs",
}


def get_language_from_file_path(file_path: str) -> Optional[str]:
    """
    Determine the programming language from a file path.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        The language identifier or None if the language is not supported.
    """
    _, ext = os.path.splitext(file_path.lower())
    return EXTENSION_TO_LANGUAGE.get(ext)


def extract_metadata_from_text(text: str, language: str = "py") -> List[Dict[str, Any]]:
    """
    Extract ADP metadata from code text.

    Args:
        text: The code text to extract metadata from.
        language: The programming language of the code text.

    Returns:
        A list of metadata dictionaries.
    """
    if language not in COMMENT_PATTERNS:
        logger.warning(f"Unsupported language: {language}")
        return []

    patterns = COMMENT_PATTERNS[language]
    metadata_blocks = []

    # Extract single line metadata
    if "single_pattern" in patterns:
        single_matches = re.finditer(patterns["single_pattern"], text)
        for match in single_matches:
            json_str = match.group(1).strip()
            try:
                metadata = json.loads(json_str)
                line_num = len(text[:match.start()].split('\n'))
                metadata_blocks.append({
                    "metadata": metadata,
                    "line": line_num,
                    "type": "single"
                })
                logger.debug(f"Found single line metadata at line {line_num}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from single line comment: {e}")

    # Extract multi-line metadata
    if "multi_pattern" in patterns:
        logger.debug(f"Searching for multiline metadata with pattern: {patterns['multi_pattern'][:50]}")
        multi_matches = re.finditer(patterns["multi_pattern"], text)
        match_count = 0
        for match in multi_matches:
            match_count += 1
            json_str = match.group(1).strip()
            logger.debug(f"Match {match_count} raw text: {json_str}")
            
            # Clean up the JSON string
            cleaned_json = json_str.strip()
            logger.debug(f"Cleaned JSON: {cleaned_json}")
            
            # Ensure the JSON string starts and ends with curly braces
            if not cleaned_json.startswith('{'):
                cleaned_json = '{' + cleaned_json
            if not cleaned_json.endswith('}'):
                cleaned_json = cleaned_json + '}'
            
            try:
                metadata = json.loads(cleaned_json)
                line_num = len(text[:match.start()].split('\n'))
                metadata_blocks.append({
                    "metadata": metadata,
                    "line": line_num,
                    "type": "multi"
                })
                logger.debug(f"Found multiline metadata at line {line_num}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {e}")
                
                # Try to fix common JSON issues
                logger.debug(f"Attempting to fix JSON: {cleaned_json}")
                fixed_json = cleaned_json.replace("'", "\"")
                
                # Check if the JSON is missing the closing brace
                if not fixed_json.rstrip().endswith('}'):
                    fixed_json = fixed_json + '}'
                
                try:
                    metadata = json.loads(fixed_json)
                    line_num = len(text[:match.start()].split('\n'))
                    metadata_blocks.append({
                        "metadata": metadata,
                        "line": line_num,
                        "type": "multi"
                    })
                    logger.debug(f"Successfully parsed fixed JSON")
                except json.JSONDecodeError:
                    # If still failing, try a more aggressive approach - extract just the domain
                    logger.debug(f"Attempting manual JSON parsing")
                    
                    # Create a minimal valid JSON with just the domain
                    minimal_metadata = {}
                    
                    # Try to extract domain using regex
                    domain_match = re.search(r'"domain"\s*:\s*"([^"]+)"', cleaned_json)
                    if domain_match:
                        domain = domain_match.group(1)
                        logger.debug(f"Manually extracted domain: {domain}")
                        minimal_metadata["domain"] = domain
                    
                    # Try to extract name using regex
                    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', cleaned_json)
                    if name_match:
                        name = name_match.group(1)
                        logger.debug(f"Manually extracted name: {name}")
                        minimal_metadata["name"] = name
                    
                    # Try to extract description using regex
                    desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', cleaned_json)
                    if desc_match:
                        description = desc_match.group(1)
                        logger.debug(f"Manually extracted description: {description}")
                        minimal_metadata["description"] = description
                    
                    # Try to extract service boundary information
                    service_match = re.search(r'"service"\s*:\s*"([^"]+)"', cleaned_json)
                    if service_match:
                        service = service_match.group(1)
                        logger.debug(f"Manually extracted service: {service}")
                        if "serviceBoundary" not in minimal_metadata:
                            minimal_metadata["serviceBoundary"] = {}
                        minimal_metadata["serviceBoundary"]["service"] = service
                    
                    team_match = re.search(r'"teamOwner"\s*:\s*"([^"]+)"', cleaned_json)
                    if team_match:
                        team = team_match.group(1)
                        logger.debug(f"Manually extracted team owner: {team}")
                        if "serviceBoundary" not in minimal_metadata:
                            minimal_metadata["serviceBoundary"] = {}
                        minimal_metadata["serviceBoundary"]["teamOwner"] = team
                    
                    if minimal_metadata:
                        line_num = len(text[:match.start()].split('\n'))
                        metadata_blocks.append({
                            "metadata": minimal_metadata,
                            "line": line_num,
                            "type": "multi"
                        })
                        logger.debug(f"Created minimal metadata from manual parsing")
        
        logger.debug(f"Found {match_count} potential metadata blocks")

    if metadata_blocks:
        # Determine scope for each metadata block
        for block in metadata_blocks:
            line_num = block["line"]
            # Simple heuristic: if it's at the top of the file, it's file scope
            if line_num <= 5:
                block["scope"] = "file"
            else:
                # Find the next function or class definition after the metadata
                lines = text.split("\n")
                for i in range(line_num, len(lines)):
                    if re.match(r'^\s*(def|class)\s+\w+', lines[i]):
                        block["scope"] = "function" if "def " in lines[i] else "class"
                        break
                else:
                    block["scope"] = "file"  # Default to file scope if no function/class found
            
            logger.debug(f"{block['type'].capitalize()} metadata at line {line_num} has scope: {block['scope']}")

    logger.info(f"Successfully parsed {len(metadata_blocks)} metadata blocks from {language} code")
    return [{"metadata": block["metadata"], "line": block["line"], "scope": block["scope"]} for block in metadata_blocks]


def determine_scope(content: str, position: int, language: str) -> str:
    """
    Determine the scope of a metadata block based on its position in the code.
    
    Args:
        content: The full content of the file.
        position: The position of the metadata block in the content.
        language: The programming language of the code.
    
    Returns:
        The scope of the metadata block as a string.
    """
    # Get the code after the metadata block
    code_after = content[position:].strip()
    
    # Default scope is file
    scope = "file"
    
    # Determine scope based on language and code after the metadata
    if language == "py":
        # Python scope detection
        if re.match(r"class\s+\w+", code_after):
            scope = "class"
        elif re.match(r"def\s+\w+", code_after):
            scope = "function"
        elif re.match(r"@\w+", code_after):
            # Check for decorators
            lines = code_after.split("\n")
            for i, line in enumerate(lines):
                if i > 0 and re.match(r"def\s+\w+", line.strip()):
                    scope = "function"
                    break
                elif i > 0 and re.match(r"class\s+\w+", line.strip()):
                    scope = "class"
                    break
        else:
            scope = "variable"
    elif language in ["js", "ts"]:
        # JavaScript/TypeScript scope detection
        if re.match(r"class\s+\w+", code_after):
            scope = "class"
        elif re.match(r"(async\s+)?function\s+\w+", code_after) or re.match(r"const\s+\w+\s*=\s*(\(.*\)|async\s*\(.*\))\s*=>", code_after):
            scope = "function"
        else:
            scope = "variable"
    elif language in ["java", "cs"]:
        # Java/C# scope detection
        if re.match(r"(public|private|protected)?\s*(static)?\s*class\s+\w+", code_after):
            scope = "class"
        elif re.match(r"(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\(", code_after):
            scope = "method"
        else:
            scope = "variable"
    
    return scope


class ADPParser:
    """Parser for extracting and validating ADP metadata from code files."""
    
    def __init__(self, schema_name: str = None):
        """
        Initialize the ADP parser.
        
        Args:
            schema_name: Name of the schema to use for validation. If None, uses the active schema.
        """
        self.schema = get_schema(schema_name)
    
    def parse_file(self, file_path: str) -> ParsedFile:
        """
        Parse a file for ADP metadata.
        
        Args:
            file_path: Path to the file to parse.
        
        Returns:
            A ParsedFile object containing the parsed metadata.
        """
        language = get_language_from_file_path(file_path)
        if not language:
            logger.warning(f"Unsupported file type: {file_path}")
            return ParsedFile(file_path=file_path, metadata_blocks=[])
        
        try:
            logger.info(f"Parsing file: {file_path} (language: {language})")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata_positions = extract_metadata_from_text(content, language)
            logger.debug(f"Found {len(metadata_positions)} potential metadata blocks")
            
            metadata_blocks = []
            
            for metadata_block in metadata_positions:
                metadata = metadata_block["metadata"]
                line_number = metadata_block["line"]
                scope = metadata_block["scope"]
                
                # Debug prints
                logger.debug(f"Metadata type: {type(metadata)}")
                logger.debug(f"Metadata content: {metadata}")
                logger.debug(f"Line number: {line_number}")
                logger.debug(f"Scope: {scope}")
                
                # Create ADPMetadata object
                metadata_obj = ADPMetadata(
                    metadata=metadata,
                    file_path=file_path,
                    line_number=line_number,
                    scope=scope
                )
                metadata_blocks.append(metadata_obj)
            
            logger.info(f"Successfully parsed {len(metadata_blocks)} metadata blocks from {file_path}")
            return ParsedFile(file_path=file_path, metadata_blocks=metadata_blocks)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return ParsedFile(file_path=file_path, metadata_blocks=[])
    
    def parse_directory(self, directory: str, recursive: bool = True) -> List[ParsedFile]:
        """
        Parse all files in a directory for ADP metadata.
        
        Args:
            directory: Directory to parse.
            recursive: Whether to recursively parse subdirectories.
        
        Returns:
            List of ParsedFile objects.
        """
        result = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if get_language_from_file_path(file_path):
                    parsed_file = self.parse_file(file_path)
                    if parsed_file.has_metadata:
                        result.append(parsed_file)
            if not recursive:
                break
        return result
    
    def validate_metadata(self, metadata: ADPMetadata) -> bool:
        """
        Validate metadata against the schema.
        
        Args:
            metadata: The metadata to validate.
        
        Returns:
            True if the metadata is valid, False otherwise.
        """
        return self.schema.validate(metadata)
    
    def get_validation_errors(self, metadata: ADPMetadata) -> List[str]:
        """
        Get validation errors for metadata.
        
        Args:
            metadata: The metadata to validate.
        
        Returns:
            List of validation error messages.
        """
        return self.schema.get_validation_errors(metadata) 