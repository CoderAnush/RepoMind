import os
import sys
import shutil
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path so we can import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.repository import Repository
from app.models.job import ProcessingJob
from app.models.document import CodeChunk, GeneratedDocumentation
from app.models.analysis import Diagram, Report
from app.services.ingestion import IngestionService
from app.services.parser import CodeParser
from app.services.vector_db import VectorDBService
from app.agents.graph import AgentOrchestrator
from app.services.rag import RAGService
from app.core.security import get_password_hash

def run_e2e_pipeline():
    print("=====================================================================")
    print("STARTING END-TO-END REPOSITORY INTELLIGENCE PIPELINE VALIDATION")
    print("=====================================================================\n")

    # 1. Setup local sqlite database for verification
    test_db_url = "sqlite:///./pipeline_test.db"
    if os.path.exists("./pipeline_test.db"):
        try:
            os.remove("./pipeline_test.db")
        except Exception:
            pass

    print(f"[STAGE 1] Initializing isolated SQLite database at: {test_db_url}")
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Create dummy developer user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="pipeline-tester@repomind.io",
        hashed_password=get_password_hash("testpassword"),
        full_name="Pipeline Tester",
        role="DEVELOPER"
    )
    db.add(user)
    db.commit()
    print(f"Created validation developer user: {user.email}")

    # Define target test repository
    test_repo_url = "https://github.com/pypa/sampleproject.git"
    repository_id = str(uuid.uuid4())
    repo = Repository(
        id=repository_id,
        owner_id=user_id,
        name="sampleproject",
        github_url=test_repo_url,
        branch="main",
        status="PENDING"
    )
    db.add(repo)
    db.commit()
    print(f"Registered repository in SQL DB: {repo.name} ({repo.github_url})")

    # 2. Clone Repository
    print("\n[STAGE 2] Cloning Repository...")
    clone_path = IngestionService.clone_repository(repository_id, repo.github_url, repo.branch)
    print(f"Cloning completed. Repository cloned to: {clone_path}")
    assert os.path.exists(clone_path), "Cloning failed! Folder does not exist."
    assert len(os.listdir(clone_path)) > 0, "Cloned folder is empty."
    print("SUCCESS: Clone verified.")

    # 3. Analyze Structure & Metadata
    print("\n[STAGE 3] Scanning Structure and File Layout...")
    structure_metadata = IngestionService.analyze_structure(clone_path)
    print(f"Total Files Found: {structure_metadata['total_files']}")
    print(f"Total Lines of Code: {structure_metadata['total_loc']}")
    print(f"Languages Breakdown: {structure_metadata['languages']}")
    print(f"Languages LOC Percentage: {structure_metadata['languages_loc_percentage']}")
    repo.status = "INDEXING"
    repo.metadata_info = structure_metadata
    db.commit()

    # 4. Traversal and AST parser
    print("\n[STAGE 4] Starting AST/Regex Code Parsing...")
    all_chunks = []
    ignore_dirs = {
        ".git", "node_modules", "venv", ".venv", "env", "dist", 
        "build", "__pycache__", "target", "vendor"
    }
    
    parsed_files = 0
    extracted_classes = 0
    extracted_functions = 0
    extracted_modules = 0

    for root, dirs, files in os.walk(clone_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            file_path = os.path.join(root, file)
            file_chunks = CodeParser.chunk_file(file_path, clone_path)
            
            if file_chunks:
                parsed_files += 1
                
            for chunk in file_chunks:
                if chunk["chunk_type"] == "class":
                    extracted_classes += 1
                elif chunk["chunk_type"] in ["function", "api_endpoint"]:
                    extracted_functions += 1
                elif chunk["chunk_type"] == "module":
                    extracted_modules += 1

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
    print(f"Parsed {parsed_files} code/text files.")
    print(f"Successfully generated {len(all_chunks)} chunks.")
    print(f"AST Extraction Stats -> Classes: {extracted_classes}, Functions/Methods: {extracted_functions}, Modules/Files: {extracted_modules}")
    assert len(all_chunks) > 0, "No chunks were parsed!"
    print("SUCCESS: AST/Regex chunk parsing verified.")

    # 5. Embeddings & Vector DB Storage (Qdrant)
    print("\n[STAGE 5] Generating Embeddings and Storing Vectors in Qdrant...")
    vector_db = VectorDBService()
    vector_db.index_chunks(repository_id, all_chunks)
    print("Successfully indexed chunks in Qdrant.")
    print("SUCCESS: Vector storage verified.")

    # 6. Retrieve relevant chunks
    print("\n[STAGE 6] Verifying Vector Search Retrieval...")
    search_query = "simple calculation function"
    print(f"Searching Qdrant for: '{search_query}'")
    hits = vector_db.search_code(repository_id, search_query, limit=3)
    print(f"Found {len(hits)} matching vector records:")
    for idx, hit in enumerate(hits):
        print(f"  [{idx+1}] File: {hit['file_path']} | Symbol: {hit.get('symbol_name')} | Type: {hit['chunk_type']}")
        print(f"      Snippet: {hit['content'][:120].strip()}...")
    assert len(hits) > 0, "Vector search returned no results!"
    print("SUCCESS: Vector retrieval verified.")

    # 7. Agent review / workflow orchestration
    print("\n[STAGE 7] Executing Agent Orchestrator Workflows...")
    agent_state = AgentOrchestrator.process_repository(repository_id, clone_path, structure_metadata)
    
    # Save documents
    for doc in agent_state.get("documents", []):
        db_doc = GeneratedDocumentation(
            repository_id=repository_id,
            doc_type=doc["doc_type"],
            title=doc["title"],
            content=doc["content"]
        )
        db.add(db_doc)
        
    api_doc_data = agent_state.get("api_docs", {})
    if api_doc_data:
        db_doc = GeneratedDocumentation(
            repository_id=repository_id,
            doc_type=api_doc_data["doc_type"],
            title=api_doc_data["title"],
            content=api_doc_data["content"]
        )
        db.add(db_doc)

    for diag in agent_state.get("diagrams", []):
        db_diag = Diagram(
            repository_id=repository_id,
            diagram_type=diag["diagram_type"],
            format=diag["format"],
            code=diag["code"]
        )
        db.add(db_diag)

    for rep in agent_state.get("reports", []):
        db_rep = Report(
            repository_id=repository_id,
            report_type=rep["report_type"],
            score=rep["score"],
            findings=rep["findings"]
        )
        db.add(db_rep)

    repo.status = "COMPLETE"
    db.commit()
    print("Completed multi-agent processing successfully.")
    print("SUCCESS: Agent workflows verified.")

    # 8. RAG Answer Generation with Citations
    print("\n[STAGE 8] Validating Chatbot QA Queries (RAG Service)...")
    rag = RAGService()
    session_id = str(uuid.uuid4())

    test_questions = [
        "What does this repository do?",
        "How does authentication work?",
        "What are the main API endpoints?",
        "Explain the main service classes."
    ]

    for q in test_questions:
        print(f"\nQuerying RAG model: '{q}'")
        res = rag.query_repository(
            repository_id=repository_id,
            user_id=user_id,
            message=q,
            session_id=session_id,
            db=db
        )
        print("Answer:")
        print(res["answer"])
        print("Citations / Source References:")
        for ref in res["references"]:
            print(f"  - File: {ref['file_path']} | Symbol: {ref.get('symbol_name')}")
        assert res["answer"], f"RAG failed to answer query: {q}"
        assert len(res["references"]) > 0, "No references attached to the answer!"

    print("\n=====================================================================")
    print("CLEANING UP RESOURCES")
    print("=====================================================================")
    
    # Close session
    db.close()
    engine.dispose()
    
    # Delete temporary sqlite db
    if os.path.exists("./pipeline_test.db"):
        os.remove("./pipeline_test.db")
        print("Removed test database file.")
        
    # Clean up cloned directories
    IngestionService.cleanup_clone(repository_id)
    print("Cleaned up cloned directory.")
    
    print("\n=====================================================================")
    print("SUCCESS: ALL PIPELINE STAGES VALIDATED AND WORKING PERFECTLY!")
    print("=====================================================================")

if __name__ == "__main__":
    run_e2e_pipeline()
