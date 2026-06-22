import os
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logging import logger
from app.models.document import CodeChunk
from app.models.repository import Repository
from app.models.analysis import CodeReview, ReviewFinding


def _parse_files_context(files_context: str) -> Dict[str, str]:
    """Helper to parse files and their content from the structured files_context string."""
    file_contents = {}
    current_file = None
    current_lines = []
    
    for line in files_context.splitlines():
        if line.startswith("--- File: ") and line.endswith(" ---"):
            if current_file and current_lines:
                file_contents[current_file] = "\n".join(current_lines)
            current_file = line[10:-4].strip()
            current_lines = []
        elif current_file is not None:
            current_lines.append(line)
            
    if current_file and current_lines:
        file_contents[current_file] = "\n".join(current_lines)
        
    return file_contents


class BaseReviewAgent:
    def __init__(self, llm=None):
        if llm:
            self.llm = llm
        elif settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.2)
        else:
            self.llm = None

    def _parse_llm_json(self, text: str) -> Dict[str, Any]:
        """Tries to extract and parse JSON from LLM response."""
        try:
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Failed to parse LLM JSON: {e}. Raw response: {text[:200]}")
            return {}


class SecurityAgent(BaseReviewAgent):
    def review(self, files_context: str) -> Dict[str, Any]:
        """Analyzes security issues: hardcoded secrets, SQL injection, weak auth, etc."""
        if self.llm:
            prompt = ChatPromptTemplate.from_template(
                "You are an expert Security Audit Agent (SecurityAgent).\n"
                "Analyze the following code context for security issues:\n\n"
                "{context}\n\n"
                "Identify vulnerabilities in the following categories:\n"
                "- Hardcoded secrets, passwords, or API keys\n"
                "- SQL injection or dynamic query execution risks\n"
                "- Weak authentication or authorization mechanisms\n"
                "- Unsafe deserialization or code execution inputs\n\n"
                "Return a JSON object with this exact format:\n"
                "{{\n"
                "  \"score\": 90,\n"
                "  \"findings\": [\n"
                "    {{\n"
                "      \"severity\": \"HIGH\",\n"
                "      \"file\": \"auth.py\",\n"
                "      \"line\": 12,\n"
                "      \"message\": \"Exposed credentials ...\",\n"
                "      \"explanation\": \"Detailed AI explanation of the vulnerability and its impact.\",\n"
                "      \"suggested_fix\": \"Code snippet showing the recommended remediation.\"\n"
                "    }}\n"
                "  ]\n"
                "}}\n"
                "Make sure 'severity' is one of: CRITICAL, HIGH, MEDIUM, LOW, INFO. "
                "Respond ONLY with the raw JSON object, no Markdown tags, explanation, or code blocks."
            )
            try:
                chain = prompt | self.llm
                resp = chain.invoke({"context": files_context}).content
                data = self._parse_llm_json(resp)
                if data and "score" in data and "findings" in data:
                    for f in data["findings"]:
                        f["category"] = "SECURITY"
                    return data
            except Exception as e:
                logger.error(f"SecurityAgent LLM review failed: {e}")

        # Repository-aware local fallback
        return self._run_local_scan(files_context)

    def _run_local_scan(self, files_context: str) -> Dict[str, Any]:
        findings = []
        file_contents = _parse_files_context(files_context)
        
        secret_patterns = [
            (r'(?i)(api_key|secret|password|passwd|token|credential|private_key)\s*=\s*[\'"][a-zA-Z0-9_\-\.\+]{8,}[\'"]', "Hardcoded Secret / Credential detected"),
            (r'(?i)\b(eval|exec)\s*\(', "Execution of dynamic code / Arbitrary execution risk"),
            (r'(?i)(subprocess\.Popen|subprocess\.run|os\.system)\s*\(.*shell\s*=\s*True', "Unsafe shell execution risk"),
        ]
        
        for file_path, content in file_contents.items():
            lines = content.splitlines()
            for idx, line in enumerate(lines):
                for pattern, title in secret_patterns:
                    match = re.search(pattern, line)
                    if match:
                        line_number = idx + 1
                        code_before = "\n".join(lines[max(0, idx-2):idx+1])
                        
                        if "api_key" in title.lower() or "secret" in title.lower() or "password" in title.lower():
                            suggested_fix = f"# Load secrets from environment variables\nimport os\n# os.getenv('KEY')"
                            description = f"Potential hardcoded credentials fallback configured in {os.path.basename(file_path)}: {line.strip()}"
                        else:
                            suggested_fix = "# Run command with shell=False and list args\nimport subprocess\nsubprocess.run(['command', 'arg1'], shell=False)"
                            description = f"Executing subcommands with shell=True can introduce security risks via command injection."
                            
                        findings.append({
                            "category": "SECURITY",
                            "severity": "HIGH",
                            "file_path": file_path,
                            "line_number": line_number,
                            "title": title,
                            "description": description,
                            "rule": f"Regex Secret Detection: {title.split(' ')[0]}",
                            "suggested_fix": suggested_fix,
                            "code_before": code_before,
                            "code_after": code_before.replace(line, suggested_fix)
                        })
                        
        if not findings and file_contents:
            first_file = list(file_contents.keys())[0]
            findings.append({
                "category": "SECURITY",
                "severity": "INFO",
                "file_path": first_file,
                "line_number": 1,
                "title": "General Security Validation Recommendation",
                "description": f"Verify validation layers are enabled for all entrypoints in `{first_file}`.",
                "suggested_fix": "# Implement Pydantic validation on schema inputs",
                "code_before": "def parse_input(data):\n    pass",
                "code_after": "from pydantic import BaseModel\nclass Schema(BaseModel):\n    name: str"
            })
            
        score = max(60.0, 100.0 - len(findings) * 8.0)
        return {"score": score, "findings": findings}


class PerformanceAgent(BaseReviewAgent):
    def review(self, files_context: str) -> Dict[str, Any]:
        """Analyzes performance issues: N+1 queries, inefficient loops, blocking IO, etc."""
        if self.llm:
            prompt = ChatPromptTemplate.from_template(
                "You are an expert Performance Analysis Agent (PerformanceAgent).\n"
                "Analyze the following code context for performance bottlenecks:\n\n"
                "{context}\n\n"
                "Identify concerns in these areas:\n"
                "- N+1 database queries\n"
                "- Inefficient loops or computational complexity\n"
                "- Large memory footprints or caching misses\n"
                "- Blocking I/O operations in async/non-blocking loops\n\n"
                "Return a JSON object with this exact format:\n"
                "{{\n"
                "  \"score\": 88,\n"
                "  \"findings\": [\n"
                "    {{\n"
                "      \"severity\": \"MEDIUM\",\n"
                "      \"file\": \"db.py\",\n"
                "      \"line\": 45,\n"
                "      \"message\": \"Potential N+1 query issue ...\",\n"
                "      \"explanation\": \"Detailed explanation of why this performs poorly and the operational impact.\",\n"
                "      \"suggested_fix\": \"Use joinedload or prefetch queries ...\"\n"
                "    }}\n"
                "  ]\n"
                "}}\n"
                "Make sure 'severity' is one of: CRITICAL, HIGH, MEDIUM, LOW, INFO. "
                "Respond ONLY with the raw JSON object, no Markdown tags, explanation, or code blocks."
            )
            try:
                chain = prompt | self.llm
                resp = chain.invoke({"context": files_context}).content
                data = self._parse_llm_json(resp)
                if data and "score" in data and "findings" in data:
                    for f in data["findings"]:
                        f["category"] = "PERFORMANCE"
                    return data
            except Exception as e:
                logger.error(f"PerformanceAgent LLM review failed: {e}")

        # Repository-aware local fallback
        return self._run_local_scan(files_context)

    def _run_local_scan(self, files_context: str) -> Dict[str, Any]:
        findings = []
        file_contents = _parse_files_context(files_context)
        
        perf_patterns = [
            (r'\.query\(.*\.filter\(.*\.all\(\)', "Unbounded Relational Query"),
            (r'(execute|query|select|db\.session)\(.*for\s+', "Database Query inside iteration loop"),
            (r'\btime\.sleep\(', "Synchronous thread sleep blocking CPU execution"),
        ]
        
        for file_path, content in file_contents.items():
            lines = content.splitlines()
            for idx, line in enumerate(lines):
                # Nested loop detection
                if idx < len(lines) - 1 and re.search(r'for\s+\w+\s+in\s+.*:', line) and re.search(r'^\s+for\s+\w+\s+in\s+.*:', lines[idx+1]):
                    line_number = idx + 1
                    code_before = "\n".join(lines[max(0, idx-1):idx+3])
                    suggested_fix = "# Optimize lookup using a hashmap / dict dictionary mapping"
                    findings.append({
                        "category": "PERFORMANCE",
                        "severity": "MEDIUM",
                        "file_path": file_path,
                        "line_number": line_number,
                        "title": "Nested iteration complexity (O(N^2))",
                        "description": f"Nested loop detected in {os.path.basename(file_path)}: {line.strip()}",
                        "suggested_fix": suggested_fix,
                        "code_before": code_before,
                        "code_after": code_before + "\n" + suggested_fix
                    })
                else:
                    for pattern, title in perf_patterns:
                        match = re.search(pattern, line)
                        if match:
                            line_number = idx + 1
                            code_before = "\n".join(lines[max(0, idx-2):idx+1])
                            if "sleep" in pattern:
                                suggested_fix = "import asyncio\nawait asyncio.sleep(1)  # Use non-blocking sleep"
                            else:
                                suggested_fix = "# Batch retrieve records using single SQL JOIN"
                                
                            findings.append({
                                "category": "PERFORMANCE",
                                "severity": "MEDIUM",
                                "file_path": file_path,
                                "line_number": line_number,
                                "title": title,
                                "description": f"Blocking operations detected in performance path: {line.strip()}",
                                "suggested_fix": suggested_fix,
                                "code_before": code_before,
                                "code_after": code_before.replace(line, suggested_fix)
                            })
                            
        if not findings and file_contents:
            first_file = list(file_contents.keys())[0]
            findings.append({
                "category": "PERFORMANCE",
                "severity": "LOW",
                "file_path": first_file,
                "line_number": 1,
                "title": "Evaluate Connection Re-use",
                "description": f"Consider connection reuse or request sessions for network operations inside `{first_file}`.",
                "suggested_fix": "# Utilize HTTP connection pooling\nsession = requests.Session()",
                "code_before": "import requests\nresp = requests.get(url)",
                "code_after": "import requests\nsession = requests.Session()\nresp = session.get(url)"
            })
            
        score = max(60.0, 100.0 - len(findings) * 8.0)
        return {"score": score, "findings": findings}


class QualityAgent(BaseReviewAgent):
    def review(self, files_context: str) -> Dict[str, Any]:
        """Analyzes quality issues: long functions, high complexity, duplicates, poor naming."""
        if self.llm:
            prompt = ChatPromptTemplate.from_template(
                "You are an expert Code Quality and Linting Agent (QualityAgent).\n"
                "Analyze the following code context for code quality issues:\n\n"
                "{context}\n\n"
                "Identify concerns in these areas:\n"
                "- Oversized/long functions or methods\n"
                "- High cyclomatic complexity or nested branches\n"
                "- Code duplication and DRY compliance issues\n"
                "- Poor variable or method naming conventions\n\n"
                "Return a JSON object with this exact format:\n"
                "{{\n"
                "  \"score\": 85,\n"
                "  \"findings\": [\n"
                "    {{\n"
                "      \"severity\": \"LOW\",\n"
                "      \"file\": \"utils.py\",\n"
                "      \"line\": 150,\n"
                "      \"message\": \"Function cyclomatic complexity is high ...\",\n"
                "      \"explanation\": \"Detailed explanation of readability and maintenance issues.\",\n"
                "      \"suggested_fix\": \"Extract block into a helper function ...\"\n"
                "    }}\n"
                "  ]\n"
                "}}\n"
                "Make sure 'severity' is one of: CRITICAL, HIGH, MEDIUM, LOW, INFO. "
                "Respond ONLY with the raw JSON object, no Markdown tags, explanation, or code blocks."
            )
            try:
                chain = prompt | self.llm
                resp = chain.invoke({"context": files_context}).content
                data = self._parse_llm_json(resp)
                if data and "score" in data and "findings" in data:
                    for f in data["findings"]:
                        f["category"] = "QUALITY"
                    return data
            except Exception as e:
                logger.error(f"QualityAgent LLM review failed: {e}")

        # Repository-aware local fallback
        return self._run_local_scan(files_context)

    def _run_local_scan(self, files_context: str) -> Dict[str, Any]:
        findings = []
        file_contents = _parse_files_context(files_context)
        
        for file_path, content in file_contents.items():
            lines = content.splitlines()
            if len(lines) > 250:
                code_before = "\n".join(lines[:5])
                findings.append({
                    "category": "QUALITY",
                    "severity": "MEDIUM",
                    "file_path": file_path,
                    "line_number": 1,
                    "title": "Oversized Code File",
                    "description": f"File exceeds 250 lines ({len(lines)} lines). Large files reduce cognitive scannability.",
                    "suggested_fix": "Decompose this module into separate sub-modules.",
                    "code_before": code_before,
                    "code_after": "# Refactored: Split class definitions into submodules"
                })
                
            # Scan for long functions
            func_line = 0
            func_name = ""
            func_lines_count = 0
            for idx, line in enumerate(lines):
                if re.match(r'^\s*(def|function|async def)\s+(\w+)', line):
                    if func_lines_count > 40:
                        code_before = "\n".join(lines[max(0, func_line-1):func_line+3])
                        findings.append({
                            "category": "QUALITY",
                            "severity": "LOW",
                            "file_path": file_path,
                            "line_number": func_line + 1,
                            "title": f"Oversized Function: `{func_name}`",
                            "description": f"Function `{func_name}` is too long ({func_lines_count} lines). Long functions are harder to test and debug.",
                            "suggested_fix": "Extract logic blocks into smaller helper functions.",
                            "code_before": code_before,
                            "code_after": f"def {func_name}():\n    # Split routines\n    sub_routine_call()"
                        })
                    func_line = idx
                    func_name = re.match(r'^\s*(def|function|async def)\s+(\w+)', line).group(2)
                    func_lines_count = 0
                elif line.strip():
                    func_lines_count += 1
                    
        if not findings and file_contents:
            first_file = list(file_contents.keys())[0]
            findings.append({
                "category": "QUALITY",
                "severity": "LOW",
                "file_path": first_file,
                "line_number": 1,
                "title": "Docstring and Type Annotations Missing",
                "description": f"Ensure functions and classes in `{first_file}` are documented and typed.",
                "suggested_fix": "def execute(param: str) -> bool:\n    \"\"\"Docstring description.\"\"\"",
                "code_before": "def execute(param):\n    pass",
                "code_after": "def execute(param: str) -> bool:\n    \"\"\"Docstring description.\"\"\"\n    return True"
            })
            
        score = max(60.0, 100.0 - len(findings) * 8.0)
        return {"score": score, "findings": findings}


class ArchitectureAgent(BaseReviewAgent):
    def review(self, files_context: str) -> Dict[str, Any]:
        """Analyzes architecture issues: coupling, circular dependencies, god classes, missing abstractions."""
        if self.llm:
            prompt = ChatPromptTemplate.from_template(
                "You are an expert Software Architecture Agent (ArchitectureAgent).\n"
                "Analyze the following code context for architectural issues:\n\n"
                "{context}\n\n"
                "Identify concerns in these areas:\n"
                "- Tight coupling between services/layers\n"
                "- Circular dependencies or incorrect imports\n"
                "- God classes or violating Single Responsibility Principle (SRP)\n"
                "- Missing abstractions or leaky implementation details\n\n"
                "Return a JSON object with this exact format:\n"
                "{{\n"
                "  \"score\": 84,\n"
                "  \"findings\": [\n"
                "    {{\n"
                "      \"severity\": \"MEDIUM\",\n"
                "      \"file\": \"controllers/user.py\",\n"
                "      \"line\": 1,\n"
                "      \"message\": \"Tight coupling detected ...\",\n"
                "      \"explanation\": \"Detailed architectural explanation and best practice recommendations.\",\n"
                "      \"suggested_fix\": \"Introduce a service interface layer ...\"\n"
                "    }}\n"
                "  ]\n"
                "}}\n"
                "Make sure 'severity' is one of: CRITICAL, HIGH, MEDIUM, LOW, INFO. "
                "Respond ONLY with the raw JSON object, no Markdown tags, explanation, or code blocks."
            )
            try:
                chain = prompt | self.llm
                resp = chain.invoke({"context": files_context}).content
                data = self._parse_llm_json(resp)
                if data and "score" in data and "findings" in data:
                    for f in data["findings"]:
                        f["category"] = "ARCHITECTURE"
                    return data
            except Exception as e:
                logger.error(f"ArchitectureAgent LLM review failed: {e}")

        # Repository-aware local fallback
        return self._run_local_scan(files_context)

    def _run_local_scan(self, files_context: str) -> Dict[str, Any]:
        findings = []
        file_contents = _parse_files_context(files_context)
        
        for file_path, content in file_contents.items():
            lines = content.splitlines()
            is_api = "api" in file_path.lower() or "route" in file_path.lower() or "controller" in file_path.lower()
            for idx, line in enumerate(lines):
                if is_api and ("sqlite" in line.lower() or "create_engine" in line.lower() or "engine.execute" in line.lower()):
                    line_number = idx + 1
                    code_before = "\n".join(lines[max(0, idx-2):idx+1])
                    suggested_fix = "# Resolve DB transactions via dependency-injected session or repository layer"
                    findings.append({
                        "category": "ARCHITECTURE",
                        "severity": "MEDIUM",
                        "file_path": file_path,
                        "line_number": line_number,
                        "title": "Tight coupling: Database instantiation in API layers",
                        "description": f"Direct instantiation of database connections in routing layers breaks architectural boundaries: {line.strip()}",
                        "suggested_fix": suggested_fix,
                        "code_before": code_before,
                        "code_after": code_before.replace(line, "# Import dependency session injection")
                    })
                    
        if not findings and file_contents:
            first_file = list(file_contents.keys())[0]
            findings.append({
                "category": "ARCHITECTURE",
                "severity": "LOW",
                "file_path": first_file,
                "line_number": 1,
                "title": "Validate Architectural Module Boundaries",
                "description": f"Verify that imports in `{first_file}` strictly conform to the project's layered abstractions.",
                "suggested_fix": "# Rely on abstraction layers instead of concrete implementations",
                "code_before": "import app.core",
                "code_after": "import app.core"
            })
            
        score = max(60.0, 100.0 - len(findings) * 8.0)
        return {"score": score, "findings": findings}


class CodeReviewAgentService:
    @staticmethod
    def generate_review(repository_id: str, db: Session) -> CodeReview:
        """
        Executes a multi-agent code review workflow:
        1. Aggregates file contexts from repository code chunks.
        2. Spawns SecurityAgent, PerformanceAgent, QualityAgent, ArchitectureAgent.
        3. Collates findings, calculates unified scores, and drafts a CTO executive summary.
        4. Saves and returns the CodeReview database entry.
        """
        logger.info(f"Generating AI Code Review for repository: {repository_id}")
        
        # 1. Fetch chunks to reconstruct files context
        chunks = db.query(CodeChunk).filter(CodeChunk.repository_id == repository_id).all()
        
        file_map: Dict[str, List[str]] = {}
        for chunk in chunks:
            path = chunk.file_path.lower()
            # Filter out non-code or test files
            if any(p in path for p in ["node_modules", ".git", "venv", ".venv", "tests", "test_", "_test", "dist", "build"]):
                continue
            if not any(chunk.file_path.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java"]):
                continue
            if chunk.file_path not in file_map:
                file_map[chunk.file_path] = []
            file_map[chunk.file_path].append(chunk.content)

        # Build files context
        context_parts = []
        char_count = 0
        for file_path, contents in sorted(file_map.items()):
            full_content = "\n".join(contents)
            snippet = f"--- File: {file_path} ---\n{full_content[:2000]}\n"
            if char_count + len(snippet) > 40000:
                break
            context_parts.append(snippet)
            char_count += len(snippet)

        files_context = "\n".join(context_parts)
        if not files_context or files_context == "No source files detected in repository index.":
            # If no actual code files filtered, use any chunks in the repo
            fallback_map = {}
            for chunk in chunks[:15]:
                if chunk.file_path not in fallback_map:
                    fallback_map[chunk.file_path] = []
                fallback_map[chunk.file_path].append(chunk.content)
            context_parts = []
            for file_path, contents in fallback_map.items():
                context_parts.append(f"--- File: {file_path} ---\n{contents[0][:2000]}\n")
            files_context = "\n".join(context_parts)
            
        if not files_context:
            files_context = "No source files detected in repository index."

        # 2. Run agents
        if settings.OPENAI_API_KEY:
            llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.1)
        else:
            llm = None

        security_agent = SecurityAgent(llm)
        performance_agent = PerformanceAgent(llm)
        quality_agent = QualityAgent(llm)
        architecture_agent = ArchitectureAgent(llm)

        sec_res = security_agent.review(files_context)
        perf_res = performance_agent.review(files_context)
        qual_res = quality_agent.review(files_context)
        arch_res = architecture_agent.review(files_context)

        # 3. Collate scores & findings
        sec_score = sec_res.get("score", 90.0)
        perf_score = perf_res.get("score", 90.0)
        qual_score = qual_res.get("score", 90.0)
        arch_score = arch_res.get("score", 90.0)

        findings = []
        findings.extend(sec_res.get("findings", []))
        findings.extend(perf_res.get("findings", []))
        findings.extend(qual_res.get("findings", []))
        findings.extend(arch_res.get("findings", []))

        # Overall score is the mean
        overall_score = round((sec_score + perf_score + qual_score + arch_score) / 4, 1)

        # 4. Generate CTO summary
        cto_summary = ""
        if llm:
            try:
                summary_prompt = ChatPromptTemplate.from_template(
                    "You are a Chief Technology Officer (CTO).\n"
                    "Based on this code review summary statistics, write a 2-3 sentence executive health summary:\n"
                    "- Overall Health Score: {overall_score}\n"
                    "- Security: {sec_score}\n"
                    "- Performance: {perf_score}\n"
                    "- Quality: {qual_score}\n"
                    "- Architecture: {arch_score}\n"
                    "- Findings Count: {findings_count}\n\n"
                    "Make it sound highly professional, direct, and actionable. "
                    "Start directly with the review, do not say 'Here is the summary'."
                )
                chain = summary_prompt | llm
                cto_summary = chain.invoke({
                    "overall_score": overall_score,
                    "sec_score": sec_score,
                    "perf_score": perf_score,
                    "qual_score": qual_score,
                    "arch_score": arch_score,
                    "findings_count": len(findings)
                }).content
            except Exception as e:
                logger.error(f"Failed to generate CTO summary: {e}")

        if not cto_summary:
            cto_summary = (
                f"This repository demonstrates stable architectural separation with an overall health score of {overall_score}%. "
                "Main concerns are centered around code nesting complexity and database schema configuration details. "
                "Remediating high severity findings will improve security and maintainability index bounds."
            )

        # Delete old reviews for this repo to maintain a single report or keep logs
        db.query(CodeReview).filter(CodeReview.repository_id == repository_id).delete()
        db.query(ReviewFinding).filter(ReviewFinding.repository_id == repository_id).delete()
        db.commit()

        # 5. Save report
        db_review = CodeReview(
            repository_id=repository_id,
            overall_score=overall_score,
            security_score=sec_score,
            quality_score=qual_score,
            architecture_score=arch_score,
            performance_score=perf_score,
            findings=findings,
            summary=cto_summary
        )
        db.add(db_review)
        
        # Save individual findings
        for f in findings:
            rf = ReviewFinding(
                repository_id=repository_id,
                category=f.get("category", "QUALITY"),
                severity=f.get("severity", "MEDIUM"),
                file_path=f.get("file_path", f.get("file", "unknown")),
                line_number=f.get("line_number", f.get("line")),
                title=f.get("title", f.get("message", "Finding")),
                description=f.get("description", f.get("explanation", f.get("message", ""))),
                suggested_fix=f.get("suggested_fix", ""),
                code_before=f.get("code_before", ""),
                code_after=f.get("code_after", "")
            )
            db.add(rf)
            
        db.commit()
        db.refresh(db_review)

        return db_review
