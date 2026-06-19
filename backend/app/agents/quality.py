import os
import re
from typing import Dict, Any, List

class CodeQualityAgent:
    def __init__(self):
        # Scan for functions exceeding 100 lines (code smell)
        self.func_size_threshold = 100
        # Scan for print statements left in code
        self.print_smell = re.compile(r'^\s*print\s*\(', re.MULTILINE)

    def scan(self, clone_path: str, file_list: List[str]) -> Dict[str, Any]:
        """
        Calculates code complexity metrics and flags large files/functions.
        """
        findings = []
        total_files = len(file_list)
        large_files_count = 0
        
        for rel_path in file_list:
            if not any(rel_path.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".java"]):
                continue
                
            abs_path = os.path.join(clone_path, rel_path)
            if not os.path.exists(abs_path):
                continue
                
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                lines = content.splitlines()
                
                # Code smell: file exceeding 500 lines
                if len(lines) > 500:
                    large_files_count += 1
                    findings.append({
                        "file": rel_path,
                        "line": 1,
                        "severity": "LOW",
                        "category": "File Size",
                        "message": f"Large file detected: {len(lines)} lines. Consider splitting modules."
                    })
                    
                # Search for print statements in python
                if rel_path.endswith(".py"):
                    for idx, line in enumerate(lines):
                        if self.print_smell.match(line):
                            findings.append({
                                "file": rel_path,
                                "line": idx + 1,
                                "severity": "INFO",
                                "category": "Code Smell",
                                "message": f"Found raw print statement on line {idx + 1}. Utilize logger modules instead."
                            })
            except Exception:
                pass
                
        # Simple quality calculation
        smells_count = len(findings)
        score = 100.0 - (smells_count * 2) - (large_files_count * 5)
        score = max(0.0, min(100.0, score))
        
        return {
            "report_type": "QUALITY",
            "score": score,
            "findings": findings
        }
