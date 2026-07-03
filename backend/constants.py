from enum import Enum

# =====================================================================
# Database State & Security Validation Enums
# =====================================================================
class ReviewStatus(str, Enum):
    """Execution state tracking for code analysis pipelines."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReviewSeverity(str, Enum):
    """Threat severity levels for engineering vulnerabilities."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewCategory(str, Enum):
    """Structured assessment targets defined by schema specifications."""
    CODE_QUALITY = "CODE_QUALITY"
    BUG_DETECTION = "BUG_DETECTION"
    SECURITY_ANALYSIS = "SECURITY_ANALYSIS"
    PERFORMANCE_ANALYSIS = "PERFORMANCE_ANALYSIS"
    BEST_PRACTICES = "BEST_PRACTICES"
    SUGGESTIONS = "SUGGESTIONS"


class SupportedLanguage(str, Enum):
    """Explicitly supported language profiles for source file parsing."""
    PYTHON = "python"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


# =====================================================================
# File Extension Mappings
# =====================================================================
ALLOWED_EXTENSIONS = {
    ".py": SupportedLanguage.PYTHON,
    ".java": SupportedLanguage.JAVA,
    ".c": SupportedLanguage.C,
    ".cpp": SupportedLanguage.CPP,
    ".cc": SupportedLanguage.CPP,
    ".js": SupportedLanguage.JAVASCRIPT,
    ".ts": SupportedLanguage.TYPESCRIPT,
    ".go": SupportedLanguage.GO,
    ".rs": SupportedLanguage.RUST,
}

# =====================================================================
# Status Message Catalog
# =====================================================================
MSG_REVIEW_SUCCESS = "Code review processed and completed successfully."
MSG_REVIEW_FAILED = "An unexpected error occurred during the code review pipeline."
MSG_FILE_TOO_LARGE = "Uploaded file exceeds the maximum allowed storage payload threshold."
MSG_UNSUPPORTED_LANG = "The submitted programming language format engine is unsupported or unknown."

DEFAULT_REVIEW_SCORE = 0
REPORT_FILE_PREFIX = "review_report_"
METADATA_LICENSE = "MIT"
