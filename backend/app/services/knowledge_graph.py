import os
import re
from typing import Dict, Any, List, Set, Tuple
from sqlalchemy.orm import Session
from app.models.document import CodeChunk

class KnowledgeGraphService:
    @classmethod
    def build_graph(cls, repository_id: str, db: Session) -> Dict[str, Any]:
        """
        Builds the Code Knowledge Graph for a given repository.
        Returns a dictionary of nodes and edges.
        """
        chunks = db.query(CodeChunk).filter(CodeChunk.repository_id == repository_id).all()
        
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, str]] = []
        
        # Helper to add node
        def add_node(name: str, n_type: str, file_path: str, content: str = ""):
            if name not in nodes:
                nodes[name] = {
                    "name": name,
                    "type": n_type,
                    "file_path": file_path,
                    "summary": content[:120].strip().replace("\n", " ") + "..."
                }

        # 1. Register File nodes and Symbol nodes first
        for chunk in chunks:
            # File node
            add_node(chunk.file_path, "file", chunk.file_path, chunk.content)
            
            # Symbol nodes (classes, functions, endpoints)
            if chunk.symbol_name:
                n_type = chunk.chunk_type
                # Refine to Service or Model if applicable
                symbol_lower = chunk.symbol_name.lower()
                if n_type == "class":
                    if any(x in symbol_lower for x in ["service", "controller", "client", "agent", "chain", "pipeline"]):
                        n_type = "service"
                    elif any(x in symbol_lower for x in ["model", "schema", "table", "entity", "dto"]):
                        n_type = "model"
                elif n_type in ["function", "api_endpoint"]:
                    if any(x in symbol_lower for x in ["service", "controller", "helper"]):
                        n_type = "service"
                        
                add_node(chunk.symbol_name, n_type, chunk.file_path, chunk.content)
                
                # Edge: File contains symbol
                edges.append({
                    "source": chunk.file_path,
                    "target": chunk.symbol_name,
                    "type": "contains"
                })

        # 2. Extract relationships: Routes, Calls, Uses, Imports
        for chunk in chunks:
            # Extract Route nodes from decorators
            # Match decorators like @app.get("/path"), @router.post("/path"), etc.
            if chunk.content:
                route_matches = re.findall(r'@\w+(?:\.\w+)?\((?:\'|")([^\'"]+)(?:\'|")', chunk.content)
                for route_path in route_matches:
                    route_node_name = f"ROUTE {route_path}"
                    add_node(route_node_name, "route", chunk.file_path, f"API Route path: {route_path}")
                    
                    # Edge: Route -> Handler Function
                    if chunk.symbol_name:
                        edges.append({
                            "source": route_node_name,
                            "target": chunk.symbol_name,
                            "type": "routes_to"
                        })

                # Extract imports and build File -> Imports -> File edges
                # dependencies array typically contains imports
                if chunk.dependencies:
                    for imp in chunk.dependencies:
                        # Clean import name (e.g. "from click.core import Command" -> "click/core")
                        clean_imp = imp.replace(".", "/").replace("\\", "/")
                        for other_file in nodes.keys():
                            if nodes[other_file]["type"] == "file" and clean_imp in other_file:
                                edges.append({
                                    "source": chunk.file_path,
                                    "target": other_file,
                                    "type": "imports"
                                })

                # Extract call graphs / function call dependencies
                # Fast static parsing: check if target_symbol name is present in chunk words
                if chunk.content:
                    words = set(re.findall(r'\b[a-zA-Z0-9_]+\b', chunk.content))
                    for target_symbol, target_node in nodes.items():
                        if target_node["type"] in ["class", "function", "service", "model"]:
                            if target_symbol == chunk.symbol_name:
                                continue
                            if target_symbol in words:
                                # Edge: caller -> callee
                                edges.append({
                                    "source": chunk.symbol_name or chunk.file_path,
                                    "target": target_symbol,
                                    "type": "calls" if target_node["type"] != "model" else "uses"
                                })

        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }

    @classmethod
    def get_auth_flow(cls, graph: Dict[str, Any]) -> List[str]:
        """
        Traces the execution path related to Authentication (e.g. login, token, oauth, credentials)
        """
        # Find auth routes or login services
        start_nodes = []
        for node in graph["nodes"]:
            name_lower = node["name"].lower()
            if node["type"] == "route" and any(x in name_lower for x in ["auth", "login", "signin", "signup"]):
                start_nodes.append(node["name"])
            elif node["type"] in ["service", "function"] and any(x in name_lower for x in ["authservice", "login", "create_token", "authenticate"]):
                start_nodes.append(node["name"])

        if not start_nodes:
            # Fallback to general route or file nodes containing auth
            for node in graph["nodes"]:
                if any(x in node["name"].lower() for x in ["auth", "login"]):
                    start_nodes.append(node["name"])
                    
        return cls._traverse_paths(graph, start_nodes)

    @classmethod
    def get_request_trace(cls, graph: Dict[str, Any], query: str) -> List[str]:
        """
        Traces execution path step-by-step for a given REST method or target API route.
        """
        # Extract HTTP verb and path if available, e.g. "POST /login"
        query_lower = query.lower()
        start_nodes = []
        
        # Look for matching Route node first
        for node in graph["nodes"]:
            if node["type"] == "route":
                route_path = node["name"].replace("ROUTE ", "").lower()
                if route_path in query_lower or query_lower in route_path:
                    start_nodes.append(node["name"])
                    
        # Fallback to matching function or service name
        if not start_nodes:
            for node in graph["nodes"]:
                if node["type"] in ["function", "service"] and node["name"].lower() in query_lower:
                    start_nodes.append(node["name"])
                    
        if not start_nodes:
            # Pick first available route
            for node in graph["nodes"]:
                if node["type"] == "route":
                    start_nodes.append(node["name"])
                    break

        return cls._traverse_paths(graph, start_nodes)

    @classmethod
    def get_dependencies(cls, graph: Dict[str, Any], node_name: str) -> Dict[str, List[str]]:
        """
        Finds modules importing X, files depending on Y, or services calling Z.
        """
        imported_by = []
        calls_this = []
        depends_on = []
        
        for edge in graph["edges"]:
            if edge["target"] == node_name:
                if edge["type"] == "imports":
                    imported_by.append(edge["source"])
                elif edge["type"] in ["calls", "routes_to", "uses"]:
                    calls_this.append(edge["source"])
            elif edge["source"] == node_name:
                depends_on.append(edge["target"])
                
        return {
            "imported_by": list(set(imported_by)),
            "calls_this": list(set(calls_this)),
            "depends_on": list(set(depends_on))
        }

    @classmethod
    def get_onboarding_guide(cls, graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates core files, entrypoints, and recommended reading order for developer onboarding.
        """
        entrypoints = []
        core_files = []
        services = []
        models = []
        
        for node in graph["nodes"]:
            name = node["name"]
            n_type = node["type"]
            
            # Entrypoints: routes, main.py, app.py, cli.py, index.ts
            if n_type == "route":
                entrypoints.append(name)
            elif n_type == "file":
                base = os.path.basename(name).lower()
                if base in ["main.py", "app.py", "cli.py", "index.ts", "server.ts", "api.py"]:
                    entrypoints.append(name)
                elif any(x in base for x in ["helper", "config", "util"]):
                    pass
                else:
                    core_files.append(name)
            elif n_type == "service":
                services.append(name)
            elif n_type == "model":
                models.append(name)

        # Build reading order: entry points -> core services -> models
        reading_order = []
        reading_order.extend(entrypoints[:4])
        reading_order.extend(services[:4])
        reading_order.extend(core_files[:4])
        reading_order.extend(models[:4])

        return {
            "entrypoints": entrypoints[:5],
            "core_files": core_files[:10],
            "reading_order": reading_order[:12]
        }

    @classmethod
    def _traverse_paths(cls, graph: Dict[str, Any], start_nodes: List[str]) -> List[str]:
        """
        BFS/DFS traversal utility to build sequential execution tracks.
        """
        visited: Set[str] = set()
        path: List[str] = []
        
        # Map source to targets
        adj_list: Dict[str, List[Tuple[str, str]]] = {}
        for edge in graph["edges"]:
            src = edge["source"]
            tgt = edge["target"]
            etype = edge["type"]
            if src not in adj_list:
                adj_list[src] = []
            adj_list[src].append((tgt, etype))

        def dfs(node: str, depth: int):
            if depth > 4 or node in visited:
                return
            visited.add(node)
            path.append(node)
            
            if node in adj_list:
                # Prioritize routes_to, then calls, then uses
                sorted_targets = sorted(adj_list[node], key=lambda x: {"routes_to": 0, "calls": 1, "uses": 2, "imports": 3}.get(x[1], 4))
                for tgt, _ in sorted_targets:
                    dfs(tgt, depth + 1)

        for start in start_nodes:
            dfs(start, 0)
            
        return path
