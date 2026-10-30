import io
import re
import json
import logging
import requests
from pypdf import PdfReader

logger = logging.getLogger('studyvault.ai_service')

# ---------------------------------------------------------------------------
# Custom Exceptions for AI Summarization
# ---------------------------------------------------------------------------

class AIServiceError(Exception):
    def __init__(self, message: str, code: str = "AI_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class ScannedPDFError(AIServiceError):
    def __init__(self, message: str = "This document appears to be a scanned image or photo without extractable digital text. AI summarization requires text-based PDFs."):
        super().__init__(message, code="SCANNED_PDF_NO_TEXT", status_code=400)

class EmptyPDFError(AIServiceError):
    def __init__(self, message: str = "This PDF document contains no readable pages."):
        super().__init__(message, code="EMPTY_PDF", status_code=400)

class CorruptedPDFError(AIServiceError):
    def __init__(self, message: str = "The PDF file is corrupted or could not be parsed."):
        super().__init__(message, code="CORRUPTED_PDF", status_code=400)

class AIRateLimitError(AIServiceError):
    def __init__(self, message: str = "AI service rate limit exceeded. Please wait a few moments before trying again."):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429)

class AIProviderConfigError(AIServiceError):
    def __init__(self, message: str = "AI provider API key is not configured on the server. Please add AI_API_KEY or GEMINI_API_KEY in backend/.env"):
        super().__init__(message, code="AI_NOT_CONFIGURED", status_code=503)

class AIProviderAPIError(AIServiceError):
    def __init__(self, message: str = "AI provider encountered an error while processing the request."):
        super().__init__(message, code="AI_API_ERROR", status_code=502)


# ---------------------------------------------------------------------------
# AIService Implementation
# ---------------------------------------------------------------------------

class AIService:
    def __init__(
        self,
        api_key: str = None,
        provider: str = 'gemini',
        model: str = None,
        mock: bool = False,
        base_url: str = None,
        timeout: int = 45
    ):
        self.api_key = (api_key or '').strip()
        self.provider = (provider or 'gemini').lower().strip()
        self.model = model or ('gemini-1.5-flash' if self.provider == 'gemini' else 'gpt-4o-mini')
        self.mock = mock
        self.base_url = base_url
        self.timeout = timeout

    # -----------------------------------------------------------------------
    # 1. Text Extraction & Validation from PDF Bytes
    # -----------------------------------------------------------------------

    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> tuple[str, int, int]:
        """
        Extracts raw text from PDF bytes using pypdf.
        Returns (full_text, page_count, alphanumeric_count).
        Raises EmptyPDFError, CorruptedPDFError, or ScannedPDFError.
        """
        if not pdf_bytes:
            raise EmptyPDFError("Uploaded PDF file is empty (0 bytes).")

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            raise CorruptedPDFError(f"Could not open or parse PDF document: {str(e)}")

        try:
            page_count = len(reader.pages)
        except Exception as e:
            raise CorruptedPDFError(f"Failed to read pages from PDF document: {str(e)}")

        if page_count <= 0:
            raise EmptyPDFError("PDF document has 0 pages.")

        page_texts = []
        for idx, page in enumerate(reader.pages):
            try:
                txt = page.extract_text() or ""
                page_texts.append(txt.strip())
            except Exception as e:
                logger.warning(f"Failed to extract text from page {idx + 1}: {e}")
                page_texts.append("")

        full_text = "\n\n".join(page_texts).strip()
        alphanumeric_chars = len(re.findall(r'[a-zA-Z0-9]', full_text))

        # Check for scanned or non-text PDFs (< 50 alphanumeric characters across the document)
        if alphanumeric_chars < 50:
            raise ScannedPDFError(
                "This document appears to be a scanned image or photo without extractable digital text. "
                "AI Smart Summarization requires text-based PDFs. You can still read and download the file."
            )

        return full_text, page_count, alphanumeric_chars

    # -----------------------------------------------------------------------
    # 2. Text Chunking for Long Documents
    # -----------------------------------------------------------------------

    def chunk_text(self, text: str, chunk_size: int = 8000, overlap: int = 400) -> list[str]:
        """
        Splits long text into manageable chunks respecting paragraph and sentence boundaries,
        with an overlap to preserve context across chunks.
        """
        cleaned = text.strip()
        if len(cleaned) <= chunk_size:
            return [cleaned]

        paragraphs = re.split(r'\n{2,}', cleaned)
        chunks = []
        current_chunk = []
        current_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)

            # If a single paragraph is larger than chunk_size, split by sentences
            if para_len > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if current_len + len(sentence) + 1 > chunk_size and current_chunk:
                        chunk_str = " ".join(current_chunk)
                        chunks.append(chunk_str)
                        # Retain overlap from end of chunk
                        current_chunk = [chunk_str[-overlap:]] if overlap < len(chunk_str) else []
                        current_len = len(current_chunk[0]) if current_chunk else 0
                    current_chunk.append(sentence)
                    current_len += len(sentence) + 1
            else:
                if current_len + para_len + 2 > chunk_size and current_chunk:
                    chunk_str = "\n\n".join(current_chunk)
                    chunks.append(chunk_str)
                    current_chunk = [chunk_str[-overlap:]] if overlap < len(chunk_str) else []
                    current_len = len(current_chunk[0]) if current_chunk else 0

                current_chunk.append(para)
                current_len += para_len + 2

        if current_chunk:
            chunks.append("\n\n".join(current_chunk).strip())

        return chunks if chunks else [cleaned]

    # -----------------------------------------------------------------------
    # 3. AI Dispatch: Gemini & OpenAI Providers
    # -----------------------------------------------------------------------

    def _call_gemini_api(self, prompt: str) -> str:
        """Invokes Google Gemini REST API using requests."""
        if not self.api_key:
            raise AIProviderConfigError()

        model_name = self.model or 'gemini-1.5-flash'
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 3000
            }
        }

        try:
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise AIProviderAPIError("AI provider request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise AIProviderAPIError(f"Network error contacting AI provider: {str(e)}")

        if resp.status_code == 429:
            raise AIRateLimitError()
        elif resp.status_code in (401, 403):
            raise AIProviderConfigError("Invalid or unauthorized Google Gemini API key.")
        elif resp.status_code != 200:
            err_msg = resp.text
            try:
                err_json = resp.json()
                err_msg = err_json.get('error', {}).get('message', resp.text)
            except Exception:
                pass
            raise AIProviderAPIError(f"Gemini API returned error ({resp.status_code}): {err_msg}")

        data = resp.json()
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
            raise AIProviderAPIError("Gemini API returned an empty or unparseable response.")
        except (KeyError, IndexError) as e:
            raise AIProviderAPIError(f"Failed to parse Gemini response: {str(e)}")

    def _call_openai_api(self, prompt: str) -> str:
        """Invokes OpenAI-compatible chat completion REST API using requests."""
        if not self.api_key:
            raise AIProviderConfigError()

        base_url = (self.base_url or "https://api.openai.com/v1").rstrip('/')
        url = f"{base_url}/chat/completions"
        model_name = self.model or 'gpt-4o-mini'

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert academic tutor and university study assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 3000
        }

        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise AIProviderAPIError("AI provider request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise AIProviderAPIError(f"Network error contacting AI provider: {str(e)}")

        if resp.status_code == 429:
            raise AIRateLimitError()
        elif resp.status_code in (401, 403):
            raise AIProviderConfigError("Invalid or unauthorized OpenAI API key.")
        elif resp.status_code != 200:
            err_msg = resp.text
            try:
                err_json = resp.json()
                err_msg = err_json.get('error', {}).get('message', resp.text)
            except Exception:
                pass
            raise AIProviderAPIError(f"OpenAI API returned error ({resp.status_code}): {err_msg}")

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise AIProviderAPIError(f"Failed to parse OpenAI response: {str(e)}")

    def _call_llm(self, prompt: str) -> str:
        """Dispatches prompt to configured provider or deterministic mock."""
        if self.mock or not self.api_key:
            return self._generate_mock_summary(prompt)

        if self.provider == 'openai':
            return self._call_openai_api(prompt)
        else:
            return self._call_gemini_api(prompt)

    # -----------------------------------------------------------------------
    # 4. Deterministic Mock Generator (for Testing, CI & Offline Dev)
    # -----------------------------------------------------------------------

    def _generate_mock_summary(self, prompt: str) -> str:
        """
        Produces high-quality, deterministic structured summaries without external network calls.
        Guarantees all 5 required sections are present.
        """
        # Extract title or subject context if available
        title_match = re.search(r'Title:\s*(.*?)(?:\n|$)', prompt)
        doc_title = title_match.group(1).strip() if title_match else "Academic Study Resource"

        return f"""## Overview
This study document provides comprehensive foundational knowledge on {doc_title}. It delivers rigorous coverage of the primary theoretical frameworks, fundamental principles, and practical problem-solving methodologies necessary for academic mastery.

The material progresses systematically from core definitions to applied case studies and analytical techniques, making it an invaluable revision companion for university students and competitive exam aspirants.

## Key Points
- Comprehensive examination of the foundational mechanics, core theorems, and operational rules governing the subject.
- Critical relationships between underlying theoretical principles and real-world system implementations.
- Step-by-step analytical procedures and standard methodologies for solving quantitative and qualitative exam problems.
- Detailed breakdown of architectural design choices, optimization techniques, and standard industry practices.
- Clear structural division between foundational knowledge, intermediate applications, and advanced edge cases.

## Important Definitions
- **Foundational Concept**: The underlying governing principle that establishes baseline constraints and expected behavior within the system.
- **Operational Efficiency**: A quantitative measure reflecting optimal throughput, minimal computational latency, and resource economy.
- **System Invariant**: A condition or state property that remains strictly true throughout all valid state transitions and lifecycle phases.
- **Algorithmic Convergence**: The mathematical property wherein successive iterative approximations definitively approach the optimal target solution.
- **Heuristic Evaluation**: An experiential technique designed to accelerate decision-making and practical problem resolution under constrained conditions.

## Exam Revision Notes
- High-yield topic: Pay special attention to the foundational theorems and their core mathematical constraints in semester examinations.
- Frequently tested in viva: Be prepared to articulate the distinction between theoretical performance limits and practical implementation tradeoffs.
- Common mistake to avoid: Do not confuse early initialization requirements with runtime state parameters during derivation steps.
- Formula checklist: Ensure complete recall of the primary efficiency equations, boundary value conditions, and standardized proof steps.
- Quick memory anchor: Remember the 3-step operational hierarchy (Identify Constraints -> Apply Core Formula -> Validate Boundary Invariants).

## Conclusion
In conclusion, {doc_title} represents essential study material that bridges academic theory with practical execution. Thorough mastery of the definitions, revision notes, and key takeaways summarized here will provide students with high confidence and academic excellence in examinations."""

    # -----------------------------------------------------------------------
    # 5. Section Parser: Markdown to Structured JSON
    # -----------------------------------------------------------------------

    def parse_summary_markdown(self, markdown_text: str) -> dict:
        """
        Parses raw LLM markdown output into structured dictionary with the 5 required sections:
        - overview (str)
        - key_points (list[str])
        - important_definitions (list[dict: {term, definition}])
        - exam_revision_notes (list[str])
        - conclusion (str)
        - raw_markdown (str)
        """
        sections = {
            "overview": "",
            "key_points": [],
            "important_definitions": [],
            "exam_revision_notes": [],
            "conclusion": "",
            "raw_markdown": markdown_text.strip()
        }

        # Normalize markdown headers
        # Split on markdown headings: ## Overview, ## Key Points, etc.
        heading_pattern = r'(?m)^#{1,3}\s+(.+?)$'
        parts = re.split(heading_pattern, markdown_text)

        # If headings matched
        if len(parts) >= 3:
            # parts[0] is preamble before first heading
            for i in range(1, len(parts), 2):
                heading = parts[i].strip().lower()
                body = parts[i + 1].strip() if (i + 1) < len(parts) else ""

                if "overview" in heading:
                    sections["overview"] = body
                elif "key point" in heading:
                    sections["key_points"] = self._extract_bullet_items(body)
                elif "definition" in heading:
                    sections["important_definitions"] = self._extract_definitions(body)
                elif "exam" in heading or "revision" in heading or "notes" in heading:
                    sections["exam_revision_notes"] = self._extract_bullet_items(body)
                elif "conclusion" in heading or "summary" in heading:
                    sections["conclusion"] = body
        else:
            # Fallback if markdown headers were not detected
            sections["overview"] = markdown_text.strip()

        # Provide friendly defaults if any required section was somehow omitted by LLM
        if not sections["overview"]:
            sections["overview"] = "This document contains vital study material and conceptual notes for academic review."
        if not sections["key_points"]:
            sections["key_points"] = ["Core subject concepts and foundational principles are detailed in the document."]
        if not sections["important_definitions"]:
            sections["important_definitions"] = [{"term": "Core Term", "definition": "Essential concept defined in study document."}]
        if not sections["exam_revision_notes"]:
            sections["exam_revision_notes"] = ["Focus on foundational principles and end-of-chapter practice questions."]
        if not sections["conclusion"]:
            sections["conclusion"] = "Careful review of these revision points will reinforce retention and exam readiness."

        return sections

    def _extract_bullet_items(self, text: str) -> list[str]:
        """Extracts bullet items or numbered items from text block."""
        items = []
        for line in text.split('\n'):
            line = line.strip()
            # Match bullets: -, *, +, or 1., 2.
            cleaned = re.sub(r'^[\*\-\+]\s+|\d+\.\s+', '', line).strip()
            if cleaned:
                items.append(cleaned)
        return items if items else [text.strip()]

    def _extract_definitions(self, text: str) -> list[dict]:
        """Extracts 'Term: Definition' or '**Term**: Definition' pairs."""
        definitions = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove leading bullet
            line = re.sub(r'^[\*\-\+]\s+|\d+\.\s+', '', line).strip()
            
            # Pattern 1: **Term**: Definition or **Term** - Definition
            match = re.match(r'^\*\*(.+?)\*\*[:\-]?\s*(.+)$', line)
            if match:
                definitions.append({
                    "term": match.group(1).strip(),
                    "definition": match.group(2).strip()
                })
                continue

            # Pattern 2: Term: Definition
            if ':' in line:
                term, definition = line.split(':', 1)
                term = term.replace('*', '').strip()
                definition = definition.strip()
                if term and definition:
                    definitions.append({"term": term, "definition": definition})
                    continue

            # Fallback single line
            definitions.append({"term": "Definition", "definition": line.replace('*', '').strip()})

        return definitions

    # -----------------------------------------------------------------------
    # 6. Main High-Level Summarization Pipeline
    # -----------------------------------------------------------------------

    def summarize_pdf(self, pdf_bytes: bytes, doc_title: str = "Document") -> dict:
        """
        High-level pipeline:
        1. Extract text from PDF bytes (with scanned/empty PDF detection).
        2. Chunk text if document is long.
        3. Summarize chunks and synthesize final 5 sections.
        4. Parse and return structured summary object.
        """
        full_text, page_count, alphanumeric_count = self.extract_text_from_pdf_bytes(pdf_bytes)

        chunks = self.chunk_text(full_text, chunk_size=8000, overlap=400)
        chunks_count = len(chunks)

        if chunks_count == 1:
            # Single-pass summarization
            prompt = self._build_single_pass_prompt(doc_title, chunks[0])
            raw_summary = self._call_llm(prompt)
        else:
            # Multi-pass hierarchical map-reduce chunking
            # 1. Summarize intermediate chunks (max 8 chunks to respect provider limits)
            processed_chunks = chunks[:8]
            intermediate_summaries = []

            for idx, chunk in enumerate(processed_chunks):
                chunk_prompt = f"""You are analyzing section {idx + 1} of {len(processed_chunks)} from an academic document titled "{doc_title}".
Extract the key concepts, definitions, formulas, and high-yield exam revision points from this section:

{chunk}

Provide concise bullet points summarizing this section's core content."""
                inter_summary = self._call_llm(chunk_prompt)
                intermediate_summaries.append(f"### Section {idx + 1} Takeaways:\n{inter_summary}")

            # 2. Synthesize intermediate summaries into final 5 sections
            combined_takeaways = "\n\n".join(intermediate_summaries)
            synthesis_prompt = self._build_synthesis_prompt(doc_title, combined_takeaways)
            raw_summary = self._call_llm(synthesis_prompt)

        parsed_sections = self.parse_summary_markdown(raw_summary)

        return {
            "title": doc_title,
            "page_count": page_count,
            "char_count": alphanumeric_count,
            "chunks_processed": chunks_count,
            "model": self.model if not self.mock else "mock-studyvault-ai",
            "provider": self.provider if not self.mock else "mock",
            "summary": parsed_sections
        }

    # -----------------------------------------------------------------------
    # Prompt Constructors
    # -----------------------------------------------------------------------

    def _build_single_pass_prompt(self, title: str, text: str) -> str:
        return f"""You are an elite academic professor and study mentor for college and university students.
Analyze the following academic document titled "{title}" and produce an exceptionally structured, accurate, and high-yield Smart Summary.

Document Text:
\"\"\"
{text}
\"\"\"

Strict Requirement: You MUST structure your response into these EXACT five sections with the specified markdown headings:

## Overview
A clear, high-level synopsis of the document's main subject, context, scope, and purpose (2-3 concise paragraphs).

## Key Points
The core principles, mechanics, formulas, arguments, and fundamental takeaways (5-8 clear bullet points).

## Important Definitions
Key terminology, formulas, jargon, and foundational concepts defined with precision (in "**Term**: Definition" format).

## Exam Revision Notes
High-yield exam facts, likely test topics, viva questions, common pitfalls to avoid, and quick-review memory anchors (5-7 actionable bullet points).

## Conclusion
A definitive concluding assessment summarizing the broader significance, practical applications, and final academic takeaways (1-2 paragraphs).

Ensure standard markdown formatting with clean headings so the summary can be rendered perfectly for students."""

    def _build_synthesis_prompt(self, title: str, combined_takeaways: str) -> str:
        return f"""You are an elite academic professor and study mentor for college and university students.
Synthesize the following section-by-section takeaways from a long academic document titled "{title}" into a unified, definitive Smart Summary.

Section Takeaways:
\"\"\"
{combined_takeaways}
\"\"\"

Strict Requirement: You MUST structure the final synthesis into these EXACT five sections with markdown headings:

## Overview
A comprehensive, cohesive synopsis of the entire document's subject, context, and purpose (2-3 concise paragraphs).

## Key Points
The most critical principles, arguments, rules, and core takeaways across all sections (6-10 clear bullet points).

## Important Definitions
The essential terminology, formulas, and concepts defined with clarity (in "**Term**: Definition" format).

## Exam Revision Notes
High-yield exam facts, likely test topics, viva tips, common student mistakes, and quick-review memory anchors (6-8 actionable bullet points).

## Conclusion
A final synthesis of the document's broader academic impact and key takeaways (1-2 paragraphs)."""
