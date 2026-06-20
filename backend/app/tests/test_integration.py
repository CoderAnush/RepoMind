import os
import pytest
import uuid
from git import Repo
from app.services.ingestion import IngestionService
from app.services.parser import CodeParser
from app.services.vector_db import VectorDBService
from app.services.rag import RAGService
from app.models.repository import Repository
from app.models.document import CodeChunk
from app.models.user import User
from app.core.security import get_password_hash

def test_end_to_end_pipeline(db, tmp_path):
    # 1. Create a dummy local Git repository to mock the remote source
    repo_dir = tmp_path / "mock_git_repo"
    repo_dir.mkdir()
    
    code_content = """
class CalculatorService:
    \"\"\"
    Main service class for mathematical computations.
    \"\"\"
    def add_numbers(self, x: int, y: int) -> int:
        \"\"\"Adds two integers together\"\"\"
        return x + y

    def subtract_numbers(self, x: int, y: int) -> int:
        \"\"\"Subtracts y from x\"\"\"
        return x - y

def health_check_endpoint():
    \"\"\"Mock API route for status check\"\"\"
    return {"status": "healthy"}
"""
    file_path = repo_dir / "service.py"
    file_path.write_text(code_content)
    
    # Initialize the Git repo and commit the code
    repo = Repo.init(repo_dir)
    # Configure default git actor if not configured
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Pipeline Integrator")
        cw.set_value("user", "email", "integrator@repomind.io")
    repo.index.add(["service.py"])
    repo.index.commit("Initial commit with mathematical service functions")
    
    # Determine the branch name (git init creates master or main)
    branch = repo.active_branch.name

    # 2. Setup user and repository metadata
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="integrator@repomind.io",
        hashed_password=get_password_hash("integrationtest"),
        full_name="Integrator Bot",
        role="DEVELOPER"
    )
    db.add(user)
    db.commit()
    
    repository_id = str(uuid.uuid4())
    db_repo = Repository(
        id=repository_id,
        owner_id=user_id,
        name="mock_git_repo",
        github_url=str(repo_dir),  # Point to the local directory repository
        branch=branch,
        status="PENDING"
    )
    db.add(db_repo)
    db.commit()

    # 3. Verify Repository Cloning succeeds
    clone_path = IngestionService.clone_repository(repository_id, db_repo.github_url, db_repo.branch)
    assert os.path.exists(clone_path), "Cloned directory does not exist"
    assert len(os.listdir(clone_path)) > 0, "Cloned directory is empty"

    # 4. Verify AST parser extracts classes, functions, and methods
    structure_metadata = IngestionService.analyze_structure(clone_path)
    assert structure_metadata["total_files"] == 1
    
    all_chunks = []
    ignore_dirs = {".git", "node_modules", "venv", ".venv", "env", "dist", "build", "__pycache__"}
    for root, dirs, files in os.walk(clone_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            full_path = os.path.join(root, file)
            file_chunks = CodeParser.chunk_file(full_path, clone_path)
            for chunk in file_chunks:
                db_chunk = CodeChunk(
                    repository_id=repository_id,
                    file_path=chunk["file_path"],
                    symbol_name=chunk.get("symbol_name"),
                    chunk_type=chunk["chunk_type"],
                    content=chunk["content"],
                    language=chunk.get("language")
                )
                db.add(db_chunk)
                all_chunks.append(chunk)
    db.commit()

    assert len(all_chunks) > 0, "No chunks were parsed from the code"
    
    chunk_types = [c["chunk_type"] for c in all_chunks]
    symbol_names = [c["symbol_name"] for c in all_chunks]

    assert "class" in chunk_types, "Failed to parse the class construct via AST"
    assert "function" in chunk_types, "Failed to parse the helper function via AST"
    assert "CalculatorService" in symbol_names, "CalculatorService class was not extracted"
    assert "add_numbers" in symbol_names, "add_numbers method was not extracted"
    assert "health_check_endpoint" in symbol_names, "health_check_endpoint function was not extracted"

    # 5. Verify Embeddings are created and stored in Qdrant
    vector_db = VectorDBService()
    vector_db.index_chunks(repository_id, all_chunks)

    # 6. Verify Retrieval returns relevant chunks
    hits = vector_db.search_code(repository_id, "adds two integers", limit=2)
    assert len(hits) > 0, "Vector search returned no results"
    assert any("add_numbers" in h["content"] for h in hits), "Failed to retrieve the expected method chunk"

    # 7. Verify RAG answer generation works with citations
    rag = RAGService()
    res = rag.query_repository(
        repository_id=repository_id,
        user_id=user_id,
        message="What does CalculatorService do?",
        session_id=str(uuid.uuid4()),
        db=db
    )

    assert res["answer"] is not None
    assert len(res["references"]) > 0
    assert any("service.py" in r["file_path"] for r in res["references"]), "Source citation missing"

    # 8. Clean up local clone files
    IngestionService.cleanup_clone(repository_id)


def test_code_review_agent_workflow(db):
    # Setup user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="reviewbot@repomind.io",
        hashed_password=get_password_hash("reviewtest"),
        full_name="Review Bot",
        role="DEVELOPER"
    )
    db.add(user)
    db.commit()

    # Setup repository
    repository_id = str(uuid.uuid4())
    db_repo = Repository(
        id=repository_id,
        owner_id=user_id,
        name="review_repo",
        github_url="https://github.com/mock/review_repo",
        branch="main",
        status="COMPLETE"
    )
    db.add(db_repo)
    db.commit()

    # Add mock code chunks
    db_chunk1 = CodeChunk(
        repository_id=repository_id,
        file_path="app/main.py",
        symbol_name="main",
        chunk_type="file",
        content="def hello_world():\n    print('Hello World')\n",
        language="Python"
    )
    db_chunk2 = CodeChunk(
        repository_id=repository_id,
        file_path="config.py",
        symbol_name="config",
        chunk_type="file",
        content="DATABASE_URL = 'postgresql://admin:password@localhost/db'\n",
        language="Python"
    )
    db.add(db_chunk1)
    db.add(db_chunk2)
    db.commit()

    # Generate review
    from app.services.code_review_agent import CodeReviewAgentService
    review = CodeReviewAgentService.generate_review(repository_id, db)

    # Assertions
    assert review is not None
    assert review.repository_id == repository_id
    assert 0 <= review.overall_score <= 100
    assert review.security_score is not None
    assert review.quality_score is not None
    assert review.performance_score is not None
    assert review.architecture_score is not None
    assert len(review.findings) > 0
    assert review.summary is not None


def test_architecture_visualization_workflow(db):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="archbot@repomind.io",
        hashed_password=get_password_hash("archtest"),
        full_name="Arch Bot",
        role="DEVELOPER"
    )
    db.add(user)
    db.commit()

    repository_id = str(uuid.uuid4())
    db_repo = Repository(
        id=repository_id,
        owner_id=user_id,
        name="arch_repo",
        github_url="https://github.com/mock/arch_repo",
        branch="main",
        status="COMPLETE"
    )
    db.add(db_repo)
    db.commit()

    # Add mock chunks to represent imports, services, and models
    db_chunk1 = CodeChunk(
        repository_id=repository_id,
        file_path="app/api/v1/auth.py",
        symbol_name="login",
        chunk_type="api_endpoint",
        content="@router.post('/login')\ndef login():\n    pass",
        language="Python",
        dependencies=["app.services.auth_service"]
    )
    db_chunk2 = CodeChunk(
        repository_id=repository_id,
        file_path="app/services/auth_service.py",
        symbol_name="AuthService",
        chunk_type="class",
        content="class AuthService:\n    def verify(self):\n        pass",
        language="Python",
        dependencies=["app.models.user"]
    )
    db_chunk3 = CodeChunk(
        repository_id=repository_id,
        file_path="app/models/user.py",
        symbol_name="User",
        chunk_type="class",
        content="class User(Base):\n    id = Column(Integer)\n",
        language="Python",
        dependencies=[]
    )
    db.add(db_chunk1)
    db.add(db_chunk2)
    db.add(db_chunk3)
    db.commit()

    from app.services.architecture_visualizer import ArchitectureVisualizer
    graph = ArchitectureVisualizer.generate_graph(repository_id, db)

    assert graph is not None
    assert graph.repository_id == repository_id
    assert "nodes" in graph.graph_data
    assert "edges" in graph.graph_data
    
    nodes = graph.graph_data["nodes"]
    node_types = [n["type"] for n in nodes]
    
    assert "route" in node_types
    assert "service" in node_types
    assert "model" in node_types
    assert "database" in node_types
    assert "frontend" in node_types
    assert "external" in node_types


def test_qdrant_repository_filter_index():
    from qdrant_client.models import PayloadSchemaType, Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    from app.services.vector_db import VectorDBService
    import uuid

    # Initialize VectorDBService to get a Qdrant client
    vector_db = VectorDBService()
    client = vector_db.client

    # Define a temporary unique collection name
    temp_col = f"repomind_test_col_{uuid.uuid4().hex[:8]}"

    try:
        # 1. Create a temporary collection
        client.create_collection(
            collection_name=temp_col,
            vectors_config=VectorParams(
                size=vector_db.vector_dim,
                distance=Distance.COSINE
            )
        )

        # 2. Create repository_id payload index (keyword type)
        client.create_payload_index(
            collection_name=temp_col,
            field_name="repository_id",
            field_schema=PayloadSchemaType.KEYWORD
        )

        # Verify index was created
        col_info = client.get_collection(collection_name=temp_col)
        is_local = "Local" in type(client._client).__name__
        if not is_local:
            assert "repository_id" in col_info.payload_schema

        # 3. Insert test vectors with repository_id payload
        test_repo_id = str(uuid.uuid4())
        other_repo_id = str(uuid.uuid4())
        point_id_1 = str(uuid.uuid4())
        point_id_2 = str(uuid.uuid4())

        client.upsert(
            collection_name=temp_col,
            points=[
                PointStruct(
                    id=point_id_1,
                    vector=[0.1] * vector_db.vector_dim,
                    payload={"repository_id": test_repo_id, "text": "target content"}
                ),
                PointStruct(
                    id=point_id_2,
                    vector=[0.1] * vector_db.vector_dim,
                    payload={"repository_id": other_repo_id, "text": "other content"}
                ),
            ]
        )

        # 4. Perform filtered search by repository_id
        search_result = client.query_points(
            collection_name=temp_col,
            query=[0.1] * vector_db.vector_dim,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="repository_id",
                        match=MatchValue(value=test_repo_id)
                    )
                ]
            ),
            limit=2
        )

        # 5. Verify search succeeds and only returns the correct point
        assert len(search_result.points) == 1
        assert search_result.points[0].id == point_id_1
        assert search_result.points[0].payload["repository_id"] == test_repo_id

    finally:
        # Clean up temporary collection
        try:
            client.delete_collection(collection_name=temp_col)
        except Exception:
            pass


