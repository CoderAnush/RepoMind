import os
import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.models.chat import ChatHistory
from app.models.repository import Repository
from app.models.document import CodeChunk, GeneratedDocumentation
from app.services.vector_db import VectorDBService
from app.services.llm_provider import LLMProviderService

class RAGService:
    def __init__(self):
        self.vector_db = VectorDBService()

    def query_repository(
        self, 
        repository_id: str, 
        user_id: str,
        message: str, 
        session_id: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Retrieves context chunks from Qdrant, calls the LLM, saves the chat messages,
        and generates source references.
        """
        logger.info(f"Querying repository {repository_id} with query: '{message}'")
        
        # 1. Search vector DB for matched code chunks with exception handling
        try:
            matched_chunks = self.vector_db.search_code(repository_id, message, limit=5)
        except Exception as e:
            logger.error(f"[RAG] Failed to search code in Qdrant: {str(e)}", exc_info=True)
            matched_chunks = []

        # 1b. DB fallback: if Qdrant returned nothing (e.g. in-memory mode), pull from SQLite
        if not matched_chunks:
            try:
                query_keywords = set(message.lower().split())
                db_chunks = db.query(CodeChunk).filter(
                    CodeChunk.repository_id == repository_id
                ).limit(200).all()
                # Score by keyword overlap
                scored = []
                for c in db_chunks:
                    content_words = set((c.content or "").lower().split())
                    overlap = len(query_keywords & content_words)
                    scored.append((overlap, c))
                scored.sort(key=lambda x: x[0], reverse=True)
                for _, c in scored[:5]:
                    matched_chunks.append({
                        "file_path": c.file_path,
                        "symbol_name": c.symbol_name,
                        "content": c.content,
                        "similarity_score": min(0.55 + scored[0][0] * 0.05, 0.85) if scored else 0.55,
                        "id": str(c.id)
                    })
                if matched_chunks:
                    logger.info(f"[RAG] Used DB keyword fallback: {len(matched_chunks)} chunks found")
            except Exception as e2:
                logger.error(f"[RAG] DB fallback also failed: {str(e2)}")

        # 2. Build context text
        context_blocks = []
        references = []
        
        for idx, chunk in enumerate(matched_chunks):
            file_path = chunk.get("file_path", "")
            symbol = chunk.get("symbol_name") or "Module"
            content = chunk.get("content", "")
            
            context_blocks.append(f"--- File: {file_path} (Symbol: {symbol}) ---\n{content}\n")
            references.append({
                "file_path": file_path,
                "symbol_name": chunk.get("symbol_name"),
                "snippet": content[:300] + "..." if len(content) > 300 else content
            })

        context_string = "\n".join(context_blocks)
        
        # 2b. Retrieve metadata & README/Overview doc
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        repo_name = repo.name if repo else "Unknown"
        metadata = repo.metadata_info or {} if repo else {}
        total_files = metadata.get("total_files", 0)
        total_loc = metadata.get("total_loc", 0)
        languages = metadata.get("languages", {})
        file_list = metadata.get("file_list", [])

        # Retrieve all file chunks to map out AST symbols and build comprehensive understanding
        file_symbols = {}
        try:
            chunks = db.query(CodeChunk).filter(CodeChunk.repository_id == repository_id).all()
            for c in chunks:
                if c.file_path not in file_symbols:
                    file_symbols[c.file_path] = []
                if c.symbol_name and c.symbol_name != "Module":
                    file_symbols[c.file_path].append((c.symbol_name, c.chunk_type))
        except Exception as e:
            logger.error(f"[RAG] Failed to retrieve code chunks: {e}")

        file_symbols_summary = []
        sorted_paths = sorted(file_symbols.keys())
        for path in sorted_paths[:150]:  # Cap to prevent giant prompt payloads
            syms = file_symbols[path]
            syms_str = ", ".join([f"{name} ({kind})" for name, kind in syms[:6]])
            if syms_str:
                file_symbols_summary.append(f"- File: {path} (Symbols: {syms_str})")
            else:
                file_symbols_summary.append(f"- File: {path}")
        file_symbols_string = "\n".join(file_symbols_summary)

        readme_content = ""
        try:
            readme_doc = db.query(GeneratedDocumentation).filter(
                GeneratedDocumentation.repository_id == repository_id,
                GeneratedDocumentation.doc_type == "README"
            ).first()
            if readme_doc:
                readme_content = readme_doc.content
            else:
                overview_doc = db.query(GeneratedDocumentation).filter(
                    GeneratedDocumentation.repository_id == repository_id,
                    GeneratedDocumentation.doc_type == "PROJECT_OVERVIEW"
                ).first()
                if overview_doc:
                    readme_content = overview_doc.content
        except Exception as e:
            logger.error(f"[RAG] Failed to query GeneratedDocumentation table: {e}")

        # Build the Code Knowledge Graph and graph-aware context
        from app.services.knowledge_graph import KnowledgeGraphService
        
        try:
            graph = KnowledgeGraphService.build_graph(repository_id, db)
        except Exception as e:
            logger.error(f"[RAG] Failed to build knowledge graph: {e}")
            graph = {"nodes": [], "edges": []}
            
        graph_context = ""
        query_lower = message.lower()
        trace_nodes = []
        is_auth = any(x in query_lower for x in ["auth", "login", "signin", "signup", "credential"])
        is_trace = any(x in query_lower for x in ["post", "get", "put", "delete", "trace", "flow"])
        is_onboard = any(x in query_lower for x in ["onboard", "read first", "reading order", "start", "fastest way"])
        is_depend = any(x in query_lower for x in ["depend", "import", "calls", "dependencies"])
        
        if is_auth:
            trace_nodes = KnowledgeGraphService.get_auth_flow(graph)
            if trace_nodes:
                graph_context += f"\nAUTHENTICATION EXECUTION TRACE:\n" + " -> ".join(trace_nodes) + "\n"
        elif is_trace:
            trace_nodes = KnowledgeGraphService.get_request_trace(graph, message)
            if trace_nodes:
                graph_context += f"\nREQUEST EXECUTION TRACE:\n" + " -> ".join(trace_nodes) + "\n"
        elif is_onboard:
            guide = KnowledgeGraphService.get_onboarding_guide(graph)
            trace_nodes = guide.get("reading_order", [])
            reading_str = " -> ".join(trace_nodes)
            graph_context += (
                f"\nDEVELOPER ONBOARDING GUIDE:\n"
                f"- Entrypoints: {', '.join(guide['entrypoints'])}\n"
                f"- Recommended Reading Order: {reading_str}\n"
                f"- Core Files: {', '.join(guide['core_files'][:5])}\n"
            )
        elif is_depend:
            # Find matching nodes
            matched_nodes = []
            for node in graph["nodes"]:
                if node["name"].lower() in query_lower:
                    matched_nodes.append(node["name"])
            
            dep_reports = []
            for node_name in matched_nodes[:3]:
                deps = KnowledgeGraphService.get_dependencies(graph, node_name)
                dep_reports.append(
                    f"Dependencies for '{node_name}':\n"
                    f"  - Imported by: {', '.join(deps['imported_by']) or 'None'}\n"
                    f"  - Called/Used by: {', '.join(deps['calls_this']) or 'None'}\n"
                    f"  - Depends on: {', '.join(deps['depends_on']) or 'None'}"
                )
                trace_nodes.extend(deps['depends_on'])
            if dep_reports:
                graph_context += "\nDEPENDENCY EXPLORATION METADATA:\n" + "\n".join(dep_reports) + "\n"

        # 3. Request LLM response using unified LLMProviderService
        system_prompt = (
            "You are an expert Software Engineer chatbot named RepoMind.\n"
            f"Repository Name: {repo_name}\n"
            f"Total Files: {total_files}\n"
            f"Total LOC: {total_loc}\n"
            f"Languages: {str(languages)}\n"
            f"File List Sample: {str(file_list[:15])}\n\n"
            f"COMPLETE FILE SYMBOLS MAP:\n{file_symbols_string}\n\n"
        )
        if graph_context:
            system_prompt += f"CODE KNOWLEDGE GRAPH CONTEXT:\n{graph_context}\n\n"
            
        if readme_content:
            system_prompt += f"REPOSITORY README / OVERVIEW:\n{readme_content}\n\n"

        system_prompt += (
            "Explain components and answer questions about this codebase using only the provided context blocks. "
            "Be precise, reference lines/files directly, and avoid guessing.\n\n"
            f"CONTEXT BLOCKS:\n{context_string}"
        )
        
        try:
            llm_response = LLMProviderService.generate_response(
                system_prompt=system_prompt,
                user_prompt=message
            )
            answer = llm_response["answer"]
        except Exception as e:
            logger.error(f"[RAG] LLM generation failed: {str(e)}", exc_info=True)
            answer = self._fallback_answer(message, references)

        # Classify answer type
        answer_type = "GENERAL_QA"
        if is_auth:
            answer_type = "AUTHENTICATION_FLOW"
        elif is_trace:
            answer_type = "REQUEST_TRACE"
        elif is_onboard:
            answer_type = "DEVELOPER_ONBOARDING"
        elif is_depend:
            answer_type = "DEPENDENCY_EXPLORATION"
        elif any(x in query_lower for x in ["database", "db access", "which models", "models are involved"]):
            answer_type = "DATABASE_INVENTORY"
        elif any(x in query_lower for x in ["explain the full project", "what does this repository do", "what is this repository", "summary"]):
            answer_type = "EXECUTIVE_SUMMARY"
        elif any(x in query_lower for x in ["architecture", "system overview", "data flow", "services"]):
            answer_type = "SYSTEM_ARCHITECTURE"

        retrieved_files = list(set([c.get("file_path") for c in matched_chunks if c.get("file_path")]))
        
        graph_nodes_visited = len(graph.get("nodes", []))
        visited_nodes_count = min(graph_nodes_visited, 12 if graph_nodes_visited else 0)
        graph_depth = 4 if visited_nodes_count > 6 else (3 if visited_nodes_count > 3 else 1)
        
        graph_trace = {
            "path": trace_nodes if trace_nodes else [os.path.basename(f) for f in retrieved_files[:5]],
            "visited_nodes": visited_nodes_count or len(retrieved_files),
            "depth": graph_depth
        }

        # Calculate Confidence Score
        max_similarity = max([c.get("similarity_score", 0.85) for c in matched_chunks]) if matched_chunks else 0.50
        base_confidence = int(max_similarity * 100)
        
        # Add adjustments
        if len(retrieved_files) >= 2:
            base_confidence += 5
        if visited_nodes_count >= 4:
            base_confidence += 5
        if len(answer) > 200:
            base_confidence += 5
            
        confidence_score = min(base_confidence, 100)
        
        confidence_label = "LOW"
        if confidence_score >= 90:
            confidence_label = "HIGH"
        elif confidence_score >= 70:
            confidence_label = "MEDIUM"

        evidence = {
            "retrieved_files": retrieved_files,
            "retrieved_chunks": [
                {
                    "id": c.get("id"),
                    "file_path": c.get("file_path"),
                    "similarity_score": round(c.get("similarity_score", 0.85), 2),
                    "symbol": c.get("symbol_name") or "Module"
                }
                for c in matched_chunks
            ],
            "graph_trace": graph_trace,
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "answer_type": answer_type
        }

        # 4. Save User Message & Assistant Answer to Database
        try:
            db_user_msg = ChatHistory(
                user_id=user_id,
                repository_id=repository_id,
                session_id=session_id,
                role="user",
                message=message
            )
            db_assistant_msg = ChatHistory(
                user_id=user_id,
                repository_id=repository_id,
                session_id=session_id,
                role="assistant",
                message=answer,
                references=references,
                evidence=evidence
            )
            
            db.add(db_user_msg)
            db.add(db_assistant_msg)
            db.commit()
        except Exception as e:
            logger.error(f"[RAG] Failed to save chat history: {str(e)}", exc_info=True)
            db.rollback()
        
        return {
            "answer": answer,
            "session_id": session_id,
            "references": references,
            "evidence": evidence
        }

    def _fallback_answer(self, query: str, references: List[Dict[str, Any]]) -> str:
        """
        Graceful local fallback answering query using matching file structures.
        """
        if not references:
            return (
                f"I searched the repository for '{query}' but couldn't locate any matching files "
                f"or code symbols. Please verify if the repository has finished indexing."
            )
            
        file_list = ", ".join([f"`{ref['file_path']}`" for ref in references])
        res = (
            f"I found the following files matching your search query: {file_list}.\n\n"
            f"Here is a snippet from one of the matches:\n"
            f"```python\n{references[0]['snippet']}\n```"
        )
        res += "\n\n**Source Files:**\n" + "\n".join([f"- {ref['file_path']}" for ref in references])
        return res
