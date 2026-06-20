import os
import re
from typing import Dict, Any, List, Set, Tuple
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.document import CodeChunk
from app.models.analysis import ArchitectureGraph


class ArchitectureVisualizer:
    @classmethod
    def generate_graph(cls, repository_id: str, db: Session) -> ArchitectureGraph:
        """
        Parses code chunks to extract and connect components:
        - Frontend, Backend, Database, External APIs (Layers)
        - Imports, API Routes, Services, DB Models, Folders (Nodes & Edges)
        """
        logger.info(f"Generating Architecture Visualization Graph for repository: {repository_id}")

        chunks = db.query(CodeChunk).filter(CodeChunk.repository_id == repository_id).all()

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # Unique IDs sets to prevent duplicates
        node_ids: Set[str] = set()
        edge_ids: Set[str] = set()

        def add_node(node_id: str, label: str, node_type: str, layer: str, properties: Dict[str, Any] = None):
            if node_id not in node_ids:
                node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": label,
                    "type": node_type,
                    "layer": layer,
                    "properties": properties or {}
                })

        def add_edge(source: str, target: str, edge_type: str, label: str = ""):
            edge_key = f"{source}->{target}"
            if edge_key not in edge_ids and source != target:
                edge_ids.add(edge_key)
                edges.append({
                    "id": f"edge_{len(edges) + 1}",
                    "source": source,
                    "target": target,
                    "type": edge_type,
                    "label": label
                })

        # ── 1. Create Core System Anchors ──────────────────────────────────────
        # Frontend, Central DB, and External API aggregates
        add_node("node_frontend", "React Frontend Client", "frontend", "frontend", {"desc": "Web application client interfaces"})
        add_node("node_database", "PostgreSQL Database", "database", "database", {"desc": "System Relational Database Engine"})
        add_node("node_external_api", "External APIs Gateway", "external", "external", {"desc": "Third-party endpoints, LLMs (OpenAI, Anthropic), GitHub"})

        # Group chunks by file path
        file_map: Dict[str, List[CodeChunk]] = {}
        for chunk in chunks:
            if chunk.file_path not in file_map:
                file_map[chunk.file_path] = []
            file_map[chunk.file_path].append(chunk)

        # Map import/module strings to matching file paths
        # E.g., 'app.services.ingestion' -> 'app/services/ingestion.py'
        import_resolver: Dict[str, str] = {}
        for file_path in file_map.keys():
            # Convert slash path to python import dot path
            dot_path = file_path.replace("\\", "/").replace(".py", "").replace("/", ".")
            import_resolver[dot_path] = file_path
            # Also register suffix versions
            parts = dot_path.split(".")
            for i in range(len(parts)):
                suffix = ".".join(parts[i:])
                import_resolver[suffix] = file_path

        # ── 2. Parse Files, Services, Routes, and Models ──────────────────────
        for file_path, file_chunks in file_map.items():
            # Create a file node (default type 'module')
            norm_path = file_path.replace("\\", "/")
            file_name = os.path.basename(norm_path)
            folder_name = os.path.dirname(norm_path) or "root"
            file_node_id = f"file_{norm_path}"
            
            # Categorize the layer
            layer = "backend"
            if any(folder in norm_path.lower() for folder in ["frontend", "src/pages", "src/components"]):
                layer = "frontend"

            add_node(file_node_id, file_name, "module", layer, {
                "file_path": norm_path,
                "folder": folder_name,
                "chunks_count": len(file_chunks)
            })

            # Check if this file imports external API clients
            file_content_lower = "".join([c.content.lower() for c in file_chunks])
            if any(cli in file_content_lower for cli in ["openai", "anthropic", "requests.", "httpx.", "axios.", "fetch("]):
                add_edge(file_node_id, "node_external_api", "calls", "External call")

            # Parse chunk details
            for chunk in file_chunks:
                # ── A. SERVICES ──
                # Name contains "Service", or inside a "services" folder, or class ending in Service
                is_service = (
                    "service" in norm_path.lower() or 
                    (chunk.symbol_name and "service" in chunk.symbol_name.lower())
                )
                if is_service and chunk.chunk_type in ["class", "function"]:
                    service_id = f"service_{norm_path}_{chunk.symbol_name}"
                    add_node(service_id, chunk.symbol_name or "Service", "service", layer, {
                        "file_path": norm_path,
                        "definition": chunk.content[:200]
                    })
                    add_edge(file_node_id, service_id, "contains", "Defines service")

                # ── B. API ROUTES ──
                # AST tagged api_endpoint, or route decorators
                is_route = (
                    chunk.chunk_type == "api_endpoint" or
                    (chunk.dependencies and any("route" in d.lower() for d in chunk.dependencies)) or
                    any("router" in line for line in chunk.content.splitlines()[:5])
                )
                if is_route and chunk.symbol_name:
                    route_id = f"route_{norm_path}_{chunk.symbol_name}"
                    route_label = f"API Endpoint: {chunk.symbol_name}"
                    
                    # Try parsing route method/path from decorators
                    method = "GET"
                    path_str = ""
                    for line in chunk.content.splitlines():
                        if "@router." in line or "@app." in line:
                            match = re.search(r'\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', line)
                            if match:
                                method = match.group(1).upper()
                                path_str = match.group(2)
                                route_label = f"{method} {path_str}"
                                break

                    add_node(route_id, route_label, "route", "backend", {
                        "method": method,
                        "path": path_str,
                        "file_path": norm_path,
                        "symbol": chunk.symbol_name
                    })
                    add_edge(file_node_id, route_id, "contains", "Defines route")
                    # Connect frontend to api routes
                    add_edge("node_frontend", route_id, "calls", "API request")

                # ── C. DATABASE MODELS ──
                # Inherits from Base, or Column() declarations
                is_model = (
                    "model" in norm_path.lower() or
                    "Column(" in chunk.content or
                    (chunk.symbol_name and "model" in chunk.symbol_name.lower())
                )
                if is_model and chunk.chunk_type == "class" and chunk.symbol_name:
                    model_id = f"model_{norm_path}_{chunk.symbol_name}"
                    add_node(model_id, chunk.symbol_name, "model", "backend", {
                        "file_path": norm_path,
                        "table_name": chunk.symbol_name.lower()
                    })
                    add_edge(file_node_id, model_id, "contains", "Defines model")
                    # Database model connects to database engine
                    add_edge(model_id, "node_database", "stored_in", "DB table")

                # ── 3. Parse Import Connections ────────────────────────────────
                if chunk.dependencies:
                    for imp in chunk.dependencies:
                        # Check if this import matches a repository file
                        matched_path = None
                        # Try exact match, then suffix check
                        if imp in import_resolver:
                            matched_path = import_resolver[imp]
                        else:
                            # Try matching sub-tokens
                            for token in imp.split("."):
                                if len(token) > 3 and token in import_resolver:
                                    matched_path = import_resolver[token]
                                    break

                        if matched_path:
                            clean_matched_path = matched_path.replace('\\', '/')
                            target_file_id = f"file_{clean_matched_path}"
                            add_edge(file_node_id, target_file_id, "imports", "Imports")

        # ── 4. Save and return graph ──────────────────────────────────────────
        graph_json = {
            "nodes": nodes,
            "edges": edges
        }

        # Clear old graph to maintain 1 graph per repo
        db.query(ArchitectureGraph).filter(ArchitectureGraph.repository_id == repository_id).delete()
        db.commit()

        db_graph = ArchitectureGraph(
            repository_id=repository_id,
            graph_data=graph_json
        )
        db.add(db_graph)
        db.commit()
        db.refresh(db_graph)

        return db_graph
