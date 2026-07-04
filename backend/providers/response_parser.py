import json
import re
from loguru import logger
from pydantic import ValidationError
from backend.providers.exceptions import ResponseParsingError
from backend.schemas.review_result import ParsedReviewResult

class ResponseParser:
    """
    Isolated data transformer mapping unstructured model strings to strong Pydantic schemas.
    Serves as the structural Trust Boundary (ADR-027) for external AI data.
    """
    
    # Bind context to the logger to match provider implementations
    _logger = logger.bind(component="parser")

    @staticmethod
    def _extract_json_string(raw_text: str) -> str:
        """
        Extracts a clean JSON string out of markdown envelopes or raw text blocks.
        """
        cleaned = raw_text.strip()
        
        # Match data wrapped inside standard markdown backticks ```json ... ``` or ``` ... ```
        markdown_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if markdown_match:
            return markdown_match.group(1).strip()
            
        # Fallback: scan greedily from the absolute first open brace to the absolute last close brace.
        # Fixed: Changed from (\{.*?\}) to (\{.*\}) to ensure nested lists/objects don't get truncated.
        brace_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if brace_match:
            return brace_match.group(1).strip()
            
        return cleaned

    @classmethod
    def parse_review_response(cls, response_content: str) -> ParsedReviewResult:
        """
        Parses raw text strings into a completely validated ParsedReviewResult object.
        
        Raises:
            ResponseParsingError: If deserialization or model validation constraints fail.
        """
        if not response_content or not response_content.strip():
            raise ResponseParsingError("Failed to parse review: Received empty text from AI engine.")

        # Extract the standalone JSON content substring block
        json_str = cls._extract_json_string(response_content)
        
        try:
            # Safely transform string to Python dictionary primitive formats
            data_dict = json.loads(json_str)
            
            # Run deep validation checking type constraints and bounds parameters
            return ParsedReviewResult(**data_dict)
            
        except json.JSONDecodeError as e:
            # Secondary recovery attempt: clean trailing whitespaces/unescaped character glitches
            try:
                cleaned_json_str = re.sub(r'\n\s*', ' ', json_str)
                data_dict = json.loads(cleaned_json_str)
                return ParsedReviewResult(**data_dict)
            except Exception:
                cls._logger.error(
                    f"JSON syntax deserialization failure: {str(e)} | "
                    f"response_length={len(response_content)} parsed_length={len(json_str)}"
                )
                raise ResponseParsingError(f"AI response text is malformed and could not be loaded as JSON: {str(e)}") from e
            
        except ValidationError as e:
            cls._logger.error(f"Pydantic business validation constraint failure: {str(e)}")
            raise ResponseParsingError(f"AI response did not adhere to required schema layout properties: {str(e)}") from e
