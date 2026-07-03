from enum import Enum

# =====================================================================
# 1️⃣ Severity Levels
# =====================================================================
class ReviewSeverity(str, Enum):
    """
    Risk evaluation tiers for bugs, architectural problems, 
    and security vulnerabilities discovered during code analysis.
    """
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# =====================================================================
# 2️⃣ Review Categories
# =====================================================================
class ReviewCategory(str, Enum):
    """
    Structured domains that the AI core must evaluate.
    """
    CODE_QUALITY = "CODE_QUALITY"
    BUG_DETECTION = "BUG_DETECTION"
    SECURITY_ANALYSIS = "SECURITY_ANALYSIS"
    PERFORMANCE_ANALYSIS = "PERFORMANCE_ANALYSIS"
    BEST_PRACTICES = "BEST_PRACTICES"
    SUGGESTIONS = "SUGGESTIONS"


# =====================================================================
# 3️⃣ Supported Languages & 4️⃣ Allowed File Extensions
# =====================================================================
class SupportedLanguage(str, Enum):
    """
    Explicitly supported programming language engines.
    """
    PYTHON = "python"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


# Mapping dictionary to resolve source file extensions to proper languages
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
# 5️⃣ Status Messages
# =====================================================================
MSG_REVIEW_SUCCESS = "Code review processed and completed successfully."
MSG_REVIEW_FAILED = "An unexpected error occurred during the code review pipeline."
MSG_FILE_TOO_LARGE = "Uploaded file exceeds the maximum allowed storage footprint payload threshold."
MSG_UNSUPPORTED_LANG = "The submitted programming language format engine is unsupported or unknown."


# =====================================================================
# 6️⃣ Default Application Values
# =====================================================================
DEFAULT_REVIEW_SCORE = 0
REPORT_FILE_PREFIX = "review_report_"


# =====================================================================
# 7️⃣ Project Metadata Defaults
# =====================================================================
METADATA_LICENSE = "MIT"
SUPPORTED_CATEGORIES_LIST = [category.value for category in ReviewCategory]
