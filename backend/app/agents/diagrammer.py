from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logging import logger

class DiagramAgent:
    def __init__(self, llm=None):
        if llm:
            self.llm = llm
        elif settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=0.1)
        else:
            self.llm = None

    def generate(self, summary: str, architecture: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates Mermaid Diagrams mapping system structural interactions.
        Generates: ARCHITECTURE, DEPENDENCY, CLASS, SEQUENCE.
        """
        logger.info("Running DiagramAgent...")
        
        symbols = metadata.get("extracted_symbols", [])
        files = metadata.get("file_list", [])
        
        # Build symbol summaries
        symbols_summary = "\n".join([
            f"- `{s['symbol_name']}` ({s['chunk_type']} in `{s['file_path']}`)"
            for s in symbols[:40]
        ])
        files_summary = "\n".join([f"- `{f}`" for f in files[:40]])

        diagrams = []

        configs = [
            {
                "type": "ARCHITECTURE",
                "prompt": (
                    "You are a Cloud Solution Diagrammer.\n"
                    "Generate a valid MERMAID system architecture graph (graph TD/LR) matching this description:\n"
                    "Stack Summary: {summary}\n"
                    "Architecture: {architecture}\n"
                    "Files:\n{files}\n"
                    "Only return the raw mermaid markdown fenced block starting with ```mermaid."
                ),
                "fallback": self._fallback_architecture
            },
            {
                "type": "DEPENDENCY",
                "prompt": (
                    "You are a Software Architect.\n"
                    "Generate a valid MERMAID dependency graph (graph TD) mapping imports/linkages between these files:\n"
                    "Files:\n{files}\n"
                    "Only return the raw mermaid markdown fenced block starting with ```mermaid."
                ),
                "fallback": self._fallback_dependency
            },
            {
                "type": "CLASS",
                "prompt": (
                    "You are an Object-Oriented Designer.\n"
                    "Generate a valid MERMAID class diagram (classDiagram) reflecting the classes and methods extracted:\n"
                    "AST Symbols:\n{symbols}\n"
                    "Only return the raw mermaid markdown fenced block starting with ```mermaid."
                ),
                "fallback": self._fallback_class
            },
            {
                "type": "SEQUENCE",
                "prompt": (
                    "You are a Systems Analyst.\n"
                    "Generate a valid MERMAID sequence diagram (sequenceDiagram) showing the main execution flow.\n"
                    "Use these main symbols:\n{symbols}\n"
                    "Only return the raw mermaid markdown fenced block starting with ```mermaid."
                ),
                "fallback": self._fallback_sequence
            }
        ]

        for config in configs:
            code = ""
            if self.llm:
                try:
                    prompt = ChatPromptTemplate.from_template(config["prompt"])
                    chain = prompt | self.llm
                    code = chain.invoke({
                        "summary": summary,
                        "architecture": architecture,
                        "files": files_summary,
                        "symbols": symbols_summary
                    }).content
                    code = self._clean_mermaid(code)
                except Exception as e:
                    logger.error(f"Failed to generate {config['type']} diagram via LLM: {str(e)}")
                    code = config["fallback"](files, symbols)
            else:
                code = config["fallback"](files, symbols)

            diagrams.append({
                "diagram_type": config["type"],
                "format": "MERMAID",
                "code": code
            })

        return diagrams

    def _clean_mermaid(self, text: str) -> str:
        if "```mermaid" in text:
            text = text.split("```mermaid")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()

    def _fallback_architecture(self, files: list, symbols: list) -> str:
        main_entry = "main.py"
        for f in files:
            if "app.py" in f or "main.py" in f or "index" in f:
                main_entry = f
                break
                
        return (
            "graph TD\n"
            f"    User([Client / User]) -->|Invokes| Entry[\"Entrypoint: {main_entry}\"]\n"
            "    Entry -->|Uses Core Code| Logic[\"Application Logic Modules\"]\n"
            "    Logic -->|Accesses| Files[(Local Files / Data Sources)]\n"
            "    Logic -->|Stores State| DB[(Database Store)]"
        )

    def _fallback_dependency(self, files: list, symbols: list) -> str:
        # Generate simple dependency flow based on actual parsed files
        lines = ["graph LR"]
        valid_files = [f for f in files if f.endswith((".py", ".js", ".ts", ".tsx"))][:6]
        
        if len(valid_files) >= 2:
            for i in range(len(valid_files) - 1):
                f1_clean = valid_files[i].replace("/", "_").replace("\\", "_").replace(".", "_").replace("-", "_")
                f2_clean = valid_files[i+1].replace("/", "_").replace("\\", "_").replace(".", "_").replace("-", "_")
                lines.append(f"    {f1_clean}[\"{valid_files[i]}\"] --> {f2_clean}[\"{valid_files[i+1]}\"]")
        else:
            lines.append("    A[\"Core Module\"] --> B[\"Helper Library\"]")
            
        return "\n".join(lines)

    def _fallback_class(self, files: list, symbols: list) -> str:
        classes = [s for s in symbols if s["chunk_type"] == "class"]
        methods = [s for s in symbols if s["chunk_type"] == "function"]
        
        lines = ["classDiagram"]
        if classes:
            for cls in classes[:3]:
                name = cls["symbol_name"]
                lines.append(f"    class {name} {{")
                # Attach some methods
                class_methods = [m for m in methods if m["file_path"] == cls["file_path"]][:2]
                for m in class_methods:
                    lines.append(f"        +{m['symbol_name']}()")
                lines.append("    }")
        else:
            lines.append("    class ServiceModule {")
            lines.append("        +execute()")
            lines.append("    }")
            
        return "\n".join(lines)

    def _fallback_sequence(self, files: list, symbols: list) -> str:
        funcs = [s for s in symbols if s["chunk_type"] == "function"]
        f1 = funcs[0]["symbol_name"] if len(funcs) > 0 else "main"
        f2 = funcs[1]["symbol_name"] if len(funcs) > 1 else "process_data"
        
        return (
            "sequenceDiagram\n"
            "    actor User as Client User\n"
            f"    participant App as Application Execution\n"
            f"    participant Func1 as function: {f1}\n"
            f"    participant Func2 as function: {f2}\n\n"
            "    User->>App: Run program commands\n"
            "    App->>Func1: Invoke entry process\n"
            "    Func1->>Func2: Call core operation\n"
            "    Func2-->>Func1: Return result value\n"
            "    Func1-->>App: Return success\n"
            "    App-->>User: Display output"
        )
