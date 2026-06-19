import os
import pytest
import uuid
from git import Repo
from app.services.ingestion import IngestionService
from app.services.parser import CodeParser
from app.services.vector_db import VectorDBService
from app.services.agent_service import AgentService
from app.models.repository import Repository
from app.models.document import GeneratedDocumentation, CodeChunk
from app.models.user import User
from app.core.security import get_password_hash

def test_generated_documentation_evaluation(db, tmp_path):
    # 1. Initialize a small local Git repo with AST targets
    repo_dir = tmp_path / "eval_git_repo"
    repo_dir.mkdir()
    
    code_content = """
class CalculatorService:
    \"\"\"
    Performs basic integer additions.
    \"\"\"
    def add_numbers(self, a: int, b: int) -> int:
        return a + b

def execute_health_check():
    return {"status": "ok"}
"""
    file_path = repo_dir / "service.py"
    file_path.write_text(code_content)
    
    repo = Repo.init(repo_dir)
    with repo.config_writer() as cw:
        cw.set_value("user", "name", "Eval Bot")
        cw.set_value("user", "email", "evalbot@repomind.io")
    repo.index.add(["service.py"])
    repo.index.commit("Initial commit with mathematical service functions")
    
    branch = repo.active_branch.name

    # 2. Setup user and repository metadata
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="evaluator@repomind.io",
        hashed_password=get_password_hash("evalpass"),
        full_name="Evaluator Bot",
        role="DEVELOPER"
    )
    db.add(user)
    db.commit()
    
    repository_id = str(uuid.uuid4())
    db_repo = Repository(
        id=repository_id,
        owner_id=user_id,
        name="eval_git_repo",
        github_url=str(repo_dir),
        branch=branch,
        status="PENDING"
    )
    db.add(db_repo)
    db.commit()

    # 3. Trigger full pipeline processing
    AgentService.run_analysis_pipeline(repository_id, db)
    
    # Reload repository state from DB
    db.refresh(db_repo)
    assert db_repo.status == "COMPLETE"

    # 4. Fetch and Evaluate the 6 Generated Documentation Types
    generated_docs = db.query(GeneratedDocumentation).filter(
        GeneratedDocumentation.repository_id == repository_id
    ).all()

    # Verify that all 6 required documentation categories are present
    doc_types = {doc.doc_type: doc.content for doc in generated_docs}
    
    required_types = [
        "README", 
        "PROJECT_OVERVIEW", 
        "INSTALLATION", 
        "USAGE", 
        "API_DOCUMENTATION", 
        "DEVELOPER_ONBOARDING"
    ]
    
    for r_type in required_types:
        assert r_type in doc_types, f"Missing documentation type: {r_type}"
        content = doc_types[r_type]
        assert len(content) > 0, f"Generated content for {r_type} is empty"

    # 5. Programmatic Evaluation: Verify actual repository files and symbols are referenced
    # Evaluation target 1: File 'service.py'
    # Evaluation target 2: Class 'CalculatorService'
    # Evaluation target 3: Method/Function 'add_numbers' or 'execute_health_check'
    
    # README should contain summary and symbol details
    readme = doc_types["README"]
    assert "service.py" in readme or "service" in readme, "README does not reference service file"
    assert "CalculatorService" in readme, "README does not reference AST class CalculatorService"
    assert "add_numbers" in readme, "README does not reference AST method add_numbers"

    # API Documentation should list classes and functions
    api_doc = doc_types["API_DOCUMENTATION"]
    assert "CalculatorService" in api_doc, "API Documentation does not reference CalculatorService"
    assert "add_numbers" in api_doc or "execute_health_check" in api_doc, "API Doc does not reference endpoints/methods"

    # Usage Guide should show code import invocation examples
    usage_doc = doc_types["USAGE"]
    assert "CalculatorService" in usage_doc or "execute_health_check" in usage_doc or "add_numbers" in usage_doc, "Usage Guide lacks invocation snippet"

    # Developer Onboarding Guide should point to primary entrypoints
    onboarding_doc = doc_types["DEVELOPER_ONBOARDING"]
    assert "service.py" in onboarding_doc or "service" in onboarding_doc, "Onboarding lacks setup entrypoint reference"
