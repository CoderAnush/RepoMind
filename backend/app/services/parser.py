import os
import ast
import re
from typing import List, Dict, Any, Optional

class PythonASTParser(ast.NodeVisitor):
    def __init__(self, file_content: str, file_path: str):
        self.file_content = file_content
        self.file_path = file_path
        self.lines = file_content.splitlines()
        self.results: List[Dict[str, Any]] = []
        self.imports: List[str] = []

    def get_source_segment(self, node: ast.AST) -> str:
        """Extracts the raw source lines for a given AST node."""
        start_line = node.lineno - 1
        end_line = getattr(node, "end_lineno", node.lineno)
        return "\n".join(self.lines[start_line:end_line])

    def get_decorators(self, node: Any) -> List[str]:
        """Helper to get decorator names."""
        decorators = []
        for dec in getattr(node, "decorator_list", []):
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                # e.g., router.get
                if isinstance(dec.value, ast.Name):
                    decorators.append(f"{dec.value.id}.{dec.attr}")
                else:
                    decorators.append(dec.attr)
            elif isinstance(dec, ast.Call):
                # e.g., router.get("/") or app.post()
                func = dec.func
                if isinstance(func, ast.Name):
                    decorators.append(func.id)
                elif isinstance(func, ast.Attribute):
                    if isinstance(func.value, ast.Name):
                        decorators.append(f"{func.value.id}.{func.attr}")
                    else:
                        decorators.append(func.attr)
        return decorators

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_code = self.get_source_segment(node)
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
                
        docstring = ast.get_docstring(node) or ""
        
        self.results.append({
            "symbol_name": node.name,
            "chunk_type": "class",
            "content": class_code,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno),
            "decorators": self.get_decorators(node),
            "docstring": docstring,
            "extends": bases,
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # We skip nested functions (functions inside classes are handled if needed, or we treat them as individual chunks)
        # Note: If the function parent is a ClassDef, we can classify it as a method.
        func_code = self.get_source_segment(node)
        decorators = self.get_decorators(node)
        docstring = ast.get_docstring(node) or ""
        
        # Check if it looks like an API endpoint
        is_endpoint = any(any(endpoint_indicator in dec for endpoint_indicator in ["get", "post", "put", "delete", "patch", "route"]) for dec in decorators)
        chunk_type = "api_endpoint" if is_endpoint else "function"

        self.results.append({
            "symbol_name": node.name,
            "chunk_type": chunk_type,
            "content": func_code,
            "line_start": node.lineno,
            "line_end": getattr(node, "end_lineno", node.lineno),
            "decorators": decorators,
            "docstring": docstring,
            "extends": [],
        })
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)  # Treat async functions similarly


class CodeParser:
    @staticmethod
    def parse_python_file(file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parses a Python file using Python's native AST compiler."""
        try:
            tree = ast.parse(file_content, filename=file_path)
            visitor = PythonASTParser(file_content, file_path)
            visitor.visit(tree)
            
            # Attach imports as dependencies to chunks
            for chunk in visitor.results:
                chunk["dependencies"] = visitor.imports
                chunk["language"] = "Python"
                chunk["file_path"] = file_path
                
            return visitor.results
        except SyntaxError as e:
            # Fallback to general parsing on syntax error
            return CodeParser.parse_file_regex(file_content, file_path, "Python")

    @staticmethod
    def parse_file_regex(file_content: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        """
        Uses regex parsing as a language-agnostic fallback to find functions, classes, and imports.
        """
        results = []
        lines = file_content.splitlines()
        
        # Simple patterns
        class_pattern = re.compile(r'^\s*(class|interface)\s+([a-zA-Z0-9_]+)', re.MULTILINE)
        function_pattern = re.compile(r'^\s*(function|async\s+function|const|let|def|func)\s+([a-zA-Z0-9_]+)\s*(\(|=\s*\(|async\s*\()')
        import_pattern = re.compile(r'^\s*(import|from|require)\s+.*')

        imports = []
        for line in lines:
            import_match = import_pattern.match(line)
            if import_match:
                imports.append(line.strip())

        # Let's chunk by logical line blocks or functions
        # For simplicity in this regex parser, let's look at functions and classes
        # and slice content till the next match or bracket closing
        content_len = len(lines)
        
        # Find all matches with line numbers
        matches = []
        for i, line in enumerate(lines):
            c_match = class_pattern.search(line)
            if c_match:
                matches.append((i, "class", c_match.group(2)))
                continue
            
            f_match = function_pattern.search(line)
            if f_match:
                matches.append((i, "function", f_match.group(2)))
                
        # Slice contents based on matches
        for idx, (line_no, m_type, name) in enumerate(matches):
            end_line = content_len
            if idx + 1 < len(matches):
                end_line = matches[idx + 1][0]
                
            chunk_content = "\n".join(lines[line_no:end_line])
            results.append({
                "symbol_name": name,
                "chunk_type": m_type,
                "content": chunk_content,
                "line_start": line_no + 1,
                "line_end": end_line,
                "decorators": [],
                "docstring": "",
                "extends": [],
                "dependencies": imports,
                "language": language,
                "file_path": file_path
            })
            
        # If no structures were found, chunk the whole file as a module
        if not results and file_content.strip():
            results.append({
                "symbol_name": os.path.basename(file_path),
                "chunk_type": "module",
                "content": file_content,
                "line_start": 1,
                "line_end": len(lines),
                "decorators": [],
                "docstring": "",
                "extends": [],
                "dependencies": imports,
                "language": language,
                "file_path": file_path
            })

        return results

    @classmethod
    def chunk_file(cls, file_path: str, clone_path: str) -> List[Dict[str, Any]]:
        """
        Reads a code file and breaks it down into semantic chunks with metadata.
        """
        rel_path = os.path.relpath(file_path, clone_path)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            return []

        if not content.strip():
            return []

        if ext == ".py":
            return cls.parse_python_file(content, rel_path)
        elif ext in [".js", ".jsx"]:
            return cls.parse_file_regex(content, rel_path, "JavaScript")
        elif ext in [".ts", ".tsx"]:
            return cls.parse_file_regex(content, rel_path, "TypeScript")
        elif ext == ".go":
            return cls.parse_file_regex(content, rel_path, "Go")
        elif ext == ".java":
            return cls.parse_file_regex(content, rel_path, "Java")
        else:
            # General fallback for configuration files, yaml, dockerfiles, shell scripts, etc.
            lang_label = ext[1:].upper() if ext.startswith(".") else "Other"
            return [{
                "symbol_name": os.path.basename(file_path),
                "chunk_type": "file",
                "content": content,
                "line_start": 1,
                "line_end": len(content.splitlines()),
                "decorators": [],
                "docstring": "",
                "extends": [],
                "dependencies": [],
                "language": lang_label,
                "file_path": rel_path
            }]
