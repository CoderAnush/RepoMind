import os
import re
from typing import Dict, Any, List

class SecurityAgent:
    def __init__(self):
        # API Keys, secrets, slack hooks, private keys
        self.secret_patterns = {
            "Generic API Key": re.compile(r'(?:key|api|token|secret|password|passwd)(?:\s*:\s*|\s*=\s*|\s*:\s*["\']|\s*=\s*["\'])[a-zA-Z0-9_\-]{16,}', re.IGNORECASE),
            "AWS Access Key": re.compile(r'AKIA[0-9A-Z]{16}'),
            "Private Key": re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'),
            "Slack Webhook": re.compile(r'https://hooks\.slack\.com/services/T[A-Z0-9_]+/B[A-Z0-9_]+/[A-Za-z0-9_]+')
        }
        # Unsafe SQL patterns (e.g. execute("SELECT ... %s" % var) or execute(f"SELECT ... {var}"))
        self.sql_injection_pattern = re.compile(r'\.(?:execute|raw)\s*\(\s*(?:f["\']|["\'].*%s|["\'].*\{\})', re.IGNORECASE)

    def scan(self, clone_path: str, file_list: List[str]) -> Dict[str, Any]:
        """
        Scans code files for secrets and SQL injection vulnerabilities.
        """
        findings = []
        
        for rel_path in file_list:
            # Only scan source files
            if not any(rel_path.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".java", ".env", ".yml", ".yaml"]):
                continue
                
            abs_path = os.path.join(clone_path, rel_path)
            if not os.path.exists(abs_path):
                continue
                
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    
                for idx, line in enumerate(lines):
                    # 1. Scan for secrets
                    for desc, regex in self.secret_patterns.items():
                        if regex.search(line):
                            findings.append({
                                "file": rel_path,
                                "line": idx + 1,
                                "severity": "HIGH",
                                "category": "Hardcoded Secret",
                                "message": f"Potential exposed {desc} detected on line {idx + 1}."
                            })
                            
                    # 2. Scan for SQL Injection
                    if self.sql_injection_pattern.search(line):
                        findings.append({
                            "file": rel_path,
                            "line": idx + 1,
                            "severity": "CRITICAL",
                            "category": "SQL Injection",
                            "message": f"Potential SQL Injection vulnerability due to dynamic query string formatting on line {idx + 1}."
                        })
            except Exception:
                pass
                
        # Calculate a simple security score out of 100
        critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
        high_count = sum(1 for f in findings if f["severity"] == "HIGH")
        
        score = 100.0 - (critical_count * 20) - (high_count * 10)
        score = max(0.0, min(100.0, score))
        
        return {
            "report_type": "SECURITY",
            "score": score,
            "findings": findings
        }
