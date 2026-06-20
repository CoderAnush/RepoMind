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
            fallback_mode = llm_response.get("fallback_mode", False)
        except Exception as e:
            logger.error(f"[RAG] LLM generation failed: {str(e)}", exc_info=True)
            fallback_mode = True
            answer = self._fallback_answer(message, references)
            
        if fallback_mode and references:
            answer = (
                f"{answer}\n\n"
                f"**[Source Files Matched]**:\n"
                f"Below is a preview of the closest matching code files parsed from the AST:\n"
                f"1. `{references[0]['file_path']}` (Symbol: `{references[0]['symbol_name']}`)\n"
                f"Snippet:\n"
                f"```python\n"
                f"{references[0]['snippet']}\n"
                f"```"
            )

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
                references=references
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
            "references": references
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
        return (
            f"**[Local Fallback Mode - No OpenAI Key Configured]**\n\n"
            f"I found the following files matching your search query: {file_list}.\n\n"
            f"Here is a snippet from one of the matches:\n"
            f"```\n{references[0]['snippet']}\n```"
        )
