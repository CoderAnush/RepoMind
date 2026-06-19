from typing import Dict, Any, List

class QAValidatorAgent:
    def validate(
        self, 
        documents: List[Dict[str, Any]], 
        reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validates completeness, structure, and readability of the generated documentation.
        """
        validations = []
        scores = []

        for doc in documents:
            content = doc.get("content", "")
            doc_type = doc.get("doc_type", "")
            
            doc_score = 100.0
            issues = []
            
            # 1. Length validation
            if len(content.split()) < 50:
                doc_score -= 30
                issues.append("Document is very short (< 50 words).")
                
            # 2. Section validations based on type
            if doc_type == "README":
                if "## Setup" not in content and "## Installation" not in content:
                    doc_score -= 20
                    issues.append("Missing standard installation/setup instructions.")
                if "## Architecture" not in content and "## Layout" not in content:
                    doc_score -= 20
                    issues.append("Missing high-level architectural overview section.")
            elif doc_type == "SETUP":
                if "Prerequisites" not in content:
                    doc_score -= 20
                    issues.append("Missing installation prerequisites.")
                    
            scores.append(doc_score)
            if issues:
                validations.append({
                    "doc_title": doc.get("title"),
                    "score": doc_score,
                    "warnings": issues
                })

        avg_score = sum(scores) / len(scores) if scores else 100.0
        
        return {
            "validation_passed": avg_score >= 70.0,
            "overall_documentation_score": round(avg_score, 2),
            "reports_validated": [r.get("report_type") for r in reports],
            "validations": validations
        }
