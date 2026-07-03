from backend.constants import ReviewCategory, ReviewSeverity

class ReviewPromptBuilder:
    """
    Registry-style Prompt Construction Component enforcing ADR-030, ADR-031, and ADR-032.
    Assembles a completely deterministic, version-controlled prompt string instructing 
    the AI to review source code and return a standardized JSON structure.
    """

    # ADR-032: Explicitly declare the prompt contract version string
    PROMPT_VERSION: str = "1.0.0"

    # Static blueprint instruction block detailing role, rules, taxonomy, and JSON specifications
    _STATIC_SYSTEM_INSTRUCTIONS: str = """You are an elite, highly critical Senior Software Engineer and Security Auditor. Your task is to perform an exhaustive, unforgiving code review of the source code provided in the context section.

### 1. IDENTITY & OBJECTIVE
Analyze the supplied file thoroughly for correctness, security vulnerabilities, performance bottlenecks, code smells, maintainability issues, and compliance with programming best practices. 

### 2. STRICT EVALUATION RULES & SCORING SCALES
You must grade the file objectively based on the following strict rubrics:

#### Overall Score Scale:
- 90.00 to 100.00: Production ready (Excellent layout, clean code, no major defects)
- 70.00 to 89.99: Minor improvements (Functional, has slight style or performance issues)
- 50.00 to 69.99: Needs significant work (Contains code smells, brittle logic, or logic flaws)
- Below 50.00: Major issues (Catastrophic architectural flaws or severe bugs)

#### Severity Tier Mapping:
- 'CRITICAL': Immediate exploit vector or critical logical breakage. Must be patched instantly.
- 'HIGH': Security risk or correctness flaw that breaks business workflows under edge conditions.
- 'MEDIUM': Performance regression, minor memory leaks, or maintainability bottlenecks.
- 'LOW': Minor linting, style non-compliance, or structural code smells.
- 'INFO': Informational suggestions, architectural optimizations, or code comments.

#### Confidence Score Definition:
- 1.0: Almost certain (Definitive bug, verifiable vulnerability, clear anti-pattern)
- 0.8: High confidence (Highly likely to cause an issue in production)
- 0.5: Moderate confidence (Heuristic match, requires manual architectural inspection)
- 0.2: Low confidence (Potential false positive, stylistic preference edge case)

#### Actionable Recommendations:
Recommendations must be immediately actionable and clear. Avoid generic advice like "Write better comments." You must explicitly reference the problematic code structure, explain why the fix works, and show the preferred fix.

### 3. MANDATORY DATA OUTPUT CONTRACT (ZERO EXPLANATION RULE)
- Return ONLY valid JSON matching the exact schema specified below.
- Do NOT wrap the JSON inside markdown code fences (e.g. do NOT use ```json ... ``` blocks).
- Do NOT include introductory messages, conversational text, footnotes, notes, or concluding text.
- Your entire response payload string must be parseable directly by a standard JSON deserializer.

#### Handling Clean Files:
If absolutely zero issues are found in the code, you must STILL return a valid JSON object. Never return plain English text. Simply return an empty list for the issues array like so: `"issues": []`.

### 4. TARGET JSON OUTPUT SCHEMA SCHEMA
Your response must strictly match this exact JSON template structure (extra or untracked fields are strictly forbidden):

{{
  "overall_score": 85.50,
  "executive_summary": "High-level markdown summary string outlining major findings, overall status, and general quality architectural trends.",
  "issues": [
    {{
      "category": "SECURITY_ANALYSIS",
      "issue_type": "SQL Injection",
      "severity": "CRITICAL",
      "title": "Short title describing the defect concisely.",
      "description": "Exhaustive technical description detailing why this specific code pattern is problematic.",
      "recommendation": "Actionable code patch or direct instructions explaining the solution and why it fixes the issue.",
      "code_snippet": "The precise code string line subset extracted directly from the target code where the problem lives.",
      "line_number": 42,
      "confidence": 0.95
    }}
  ]
}}"""

    @classmethod
    def build_review_prompt(cls, filename: str, language: str, source_code: str) -> str:
        """
        Combines the static core system instructions with the dynamic file context payload.
        
        Args:
            filename: The name of the target file being evaluated.
            language: The resolved programming language profile name.
            source_code: The raw source code contents string payload.
            
        Returns:
            A clean, deterministic prompt string ready for transmission.
        """
        # Collect dynamic enum targets from your application source of truth to inject into the text
        allowed_severities = ", ".join([f"'{s.value}'" for s in ReviewSeverity])
        allowed_categories = ", ".join([f"'{c.value}'" for c in ReviewCategory])

        # Dynamic Section Construction
        dynamic_context = f"""### 5. DYNAMIC TARGET CONTEXT (THE DATA ASSET)
- Filename: {filename}
- Programming Language: {language}
- Enforced Allowed Severities: [{allowed_severities}]
- Enforced Allowed Categories: [{allowed_categories}]

### 6. TARGET FILE SOURCE CODE TO REVIEW
{source_code}
"""
        # Assemble Static Instructions + Dynamic Context into the final unified string prompt
        return f"{cls._STATIC_SYSTEM_INSTRUCTIONS}\n\n{dynamic_context}"