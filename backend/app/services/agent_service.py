import os
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.repository import Repository
from app.models.job import ProcessingJob
from app.models.document import CodeChunk, GeneratedDocumentation
from app.models.analysis import Diagram, Report
from app.services.ingestion import IngestionService
from app.services.parser import CodeParser
from app.services.vector_db import VectorDBService
from app.agents.graph import AgentOrchestrator

class AgentService:
    @staticmethod
    def run_analysis_pipeline(repository_id: str, db: Session) -> None:
        """
        Executes the end-to-end repository ingestion, code parsing, vector indexing,
        and multi-agent analysis pipeline.
        """
        logger.info(f"Starting analysis pipeline for repository: {repository_id}")
        
        # 1. Initialize Job
        job = ProcessingJob(repository_id=repository_id, status="PROCESSING", step="CLONING")
        db.add(job)
        db.commit()
        db.refresh(job)
        
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            logger.error(f"Repository {repository_id} not found in database.")
            job.status = "FAILED"
            job.error_message = "Repository metadata record missing."
            db.commit()
            return
            
        repo.status = "CLONING"
        db.commit()
        
        clone_path = ""
        try:
            # 2. Clone repository
            clone_path = IngestionService.clone_repository(repository_id, repo.github_url, repo.branch)
            
            # 3. Analyze high-level structure (metadata)
            job.step = "PARSING"
            repo.status = "INDEXING"
            db.commit()
            
            structure_metadata = IngestionService.analyze_structure(clone_path)
            repo.metadata_info = structure_metadata
            db.commit()
            
            # 4. Traversal and AST chunk parsing
            logger.info("Traversing file layout to extract chunks...")
            all_chunks = []
            
            # Ignore common directories during parser traversal
            ignore_dirs = {
                ".git", "node_modules", "venv", ".venv", "env", "dist", 
                "build", "__pycache__", "target", "vendor"
            }
            
            for root, dirs, files in os.walk(clone_path):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    file_path = os.path.join(root, file)
                    # Parse code chunks
                    file_chunks = CodeParser.chunk_file(file_path, clone_path)
                    
                    for chunk in file_chunks:
                        # Write code chunk to postgres
                        db_chunk = CodeChunk(
                            repository_id=repository_id,
                            file_path=chunk["file_path"],
                            symbol_name=chunk.get("symbol_name"),
                            chunk_type=chunk["chunk_type"],
                            content=chunk["content"],
                            language=chunk.get("language"),
                            dependencies=chunk.get("dependencies")
                        )
                        db.add(db_chunk)
                        all_chunks.append(chunk)
            
            db.commit()
            logger.info(f"Extracted and saved {len(all_chunks)} code chunks in SQL DB.")

            # 5. Embedding Vector Indexing (Qdrant)
            job.step = "EMBEDDING"
            db.commit()
            
            vector_db = VectorDBService()
            vector_db.index_chunks(repository_id, all_chunks)
            
            # Enrich structure metadata with extracted symbols
            structure_metadata["extracted_symbols"] = [
                {
                    "symbol_name": c.get("symbol_name"),
                    "chunk_type": c.get("chunk_type"),
                    "file_path": c.get("file_path")
                }
                for c in all_chunks if c.get("symbol_name")
            ]
            
            agent_state = AgentOrchestrator.process_repository(repository_id, clone_path, structure_metadata)
            
            # Save generated documents (README, SETUP guides)
            for doc in agent_state.get("documents", []):
                db_doc = GeneratedDocumentation(
                    repository_id=repository_id,
                    doc_type=doc["doc_type"],
                    title=doc["title"],
                    content=doc["content"]
                )
                db.add(db_doc)
                
            # Add API docs separately
            api_doc_data = agent_state.get("api_docs", {})
            if api_doc_data:
                db_doc = GeneratedDocumentation(
                    repository_id=repository_id,
                    doc_type=api_doc_data["doc_type"],
                    title=api_doc_data["title"],
                    content=api_doc_data["content"]
                )
                db.add(db_doc)

            # Save generated architecture diagrams
            for diag in agent_state.get("diagrams", []):
                db_diag = Diagram(
                    repository_id=repository_id,
                    diagram_type=diag["diagram_type"],
                    format=diag["format"],
                    code=diag["code"]
                )
                db.add(db_diag)

            # Save scans and reports (Security, Quality)
            for rep in agent_state.get("reports", []):
                db_rep = Report(
                    repository_id=repository_id,
                    report_type=rep["report_type"],
                    score=rep["score"],
                    findings=rep["findings"]
                )
                db.add(db_rep)
                
            # Finalize Job and Repo success
            job.status = "SUCCESS"
            job.step = "COMPLETE"
            repo.status = "COMPLETE"
            db.commit()
            logger.info(f"Ingestion pipeline finished successfully for repository: {repository_id}")
            
        except Exception as e:
            db.rollback()
            job.status = "FAILED"
            job.error_message = str(e)
            repo.status = "FAILED"
            db.commit()
            logger.error(f"Failed analysis pipeline for repository {repository_id}: {str(e)}", exc_info=True)
            
        finally:
            # 7. Cleanup scratch local clones
            try:
                IngestionService.cleanup_clone(repository_id)
            except Exception:
                pass
