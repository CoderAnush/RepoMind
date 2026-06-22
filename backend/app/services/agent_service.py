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
            
            # 4. Traversal, AST chunk parsing, and Vector Indexing (batch-optimized)
            logger.info("Traversing file layout to extract chunks and index...")
            vector_db = VectorDBService()
            
            batch_chunks = []
            batch_db_chunks = []
            processed_files = 0
            total_chunks_indexed = 0
            
            # File extensions to ignore (binary and other heavy non-code formats)
            binary_extensions = {
                '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz',
                '.7z', '.exe', '.dll', '.so', '.dylib', '.pyc', '.pyd', '.class', '.jar',
                '.war', '.db', '.sqlite', '.sqlite3', '.mp3', '.mp4', '.avi', '.mov',
                '.ttf', '.woff', '.woff2', '.eot', '.svg', '.bin', '.dat', '.xlsx',
                '.docx', '.pptx', '.csv', '.parquet', '.lib', '.a', '.obj', '.o',
                # ML model / data serialization formats (contain NUL bytes)
                '.pkl', '.pickle', '.npy', '.npz', '.h5', '.hdf5', '.joblib',
                '.model', '.weights', '.pt', '.pth', '.onnx', '.pb',
                '.feather', '.arrow', '.proto', '.safetensors', '.keras',
            }
            
            ignore_dirs = {
                ".git", "node_modules", "venv", ".venv", "env", "dist", 
                "build", "__pycache__", "target", "vendor", ".idea", ".vscode",
                ".pytest_cache", ".mypy_cache", ".tox"
            }
            
            symbol_metadata_list = []
            
            stop_traversal = False
            for root, dirs, files in os.walk(clone_path):
                if stop_traversal:
                    break
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    if processed_files >= 120:
                        stop_traversal = True
                        break
                    file_path = os.path.join(root, file)
                    
                    # Safeguard 1: Skip if binary extension
                    _, ext = os.path.splitext(file)
                    if ext.lower() in binary_extensions:
                        continue
                        
                    # Safeguard 2: Skip very large files (> 500 KB) to prevent timeout / OOM
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > 500 * 1024:  # 500 KB
                            logger.info(f"Skipping large file: {file_path} ({file_size / 1024:.1f} KB)")
                            continue
                    except Exception:
                        continue
                    
                    # Parse code chunks
                    try:
                        file_chunks = CodeParser.chunk_file(file_path, clone_path)
                    except Exception as e:
                        logger.warning(f"Error parsing file {file_path}: {e}")
                        file_chunks = []
                    
                    for chunk in file_chunks:
                        # Sanitize NUL bytes (\x00) — PostgreSQL rejects them in text columns
                        # This occurs with repos containing pickle files or binary-embedded notebooks
                        clean_content = chunk["content"].replace('\x00', '') if chunk.get("content") else ""
                        clean_symbol = (chunk.get("symbol_name") or "").replace('\x00', '') or None
                        clean_path = (chunk.get("file_path") or "").replace('\x00', '')

                        if not clean_content.strip():
                            continue  # Skip chunks that become empty after NUL removal

                        db_chunk = CodeChunk(
                            repository_id=repository_id,
                            file_path=clean_path,
                            symbol_name=clean_symbol,
                            chunk_type=chunk["chunk_type"],
                            content=clean_content,
                            language=chunk.get("language"),
                            dependencies=chunk.get("dependencies")
                        )
                        batch_db_chunks.append(db_chunk)
                        batch_chunks.append({**chunk, "content": clean_content})
                        
                        if chunk.get("symbol_name") and len(symbol_metadata_list) < 1000:
                            symbol_metadata_list.append({
                                "symbol_name": chunk.get("symbol_name"),
                                "chunk_type": chunk.get("chunk_type"),
                                "file_path": chunk.get("file_path")
                            })
                            
                    processed_files += 1
                    
                    # Process and commit in batches of 50 chunks to prevent memory bloat
                    if len(batch_chunks) >= 50:
                        # 1. Index in Qdrant
                        vector_db.index_chunks(repository_id, batch_chunks)
                        total_chunks_indexed += len(batch_chunks)
                        
                        # 2. Add to postgres & commit
                        for dbc in batch_db_chunks:
                            db.add(dbc)
                        db.commit()
                        
                        # Target-expunge code chunks to free memory without detaching Repository or Job
                        for dbc in batch_db_chunks:
                            try:
                                db.expunge(dbc)
                            except Exception:
                                pass
                        
                        logger.info(f"Progress: processed {processed_files} files, indexed {total_chunks_indexed} chunks.")
                        
                        # Clear batch lists
                        batch_chunks.clear()
                        batch_db_chunks.clear()

            # Process remaining chunks
            if batch_chunks:
                vector_db.index_chunks(repository_id, batch_chunks)
                total_chunks_indexed += len(batch_chunks)
                for dbc in batch_db_chunks:
                    db.add(dbc)
                db.commit()
                for dbc in batch_db_chunks:
                    try:
                        db.expunge(dbc)
                    except Exception:
                        pass
                logger.info(f"Progress final: processed {processed_files} files, indexed {total_chunks_indexed} chunks.")
                batch_chunks.clear()
                batch_db_chunks.clear()

            # 5. Update metadata and step for Agents
            job.step = "EMBEDDING"
            db.commit()
            
            # Enrich structure metadata with extracted symbols (lightweight)
            structure_metadata["extracted_symbols"] = symbol_metadata_list

            
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
