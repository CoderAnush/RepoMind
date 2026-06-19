from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from app.core.logging import logger

# Import agents
from app.agents.analyzer import RepoAnalysisAgent
from app.agents.architecture import ArchitectureAgent
from app.agents.doc_generator import DocGeneratorAgent
from app.agents.api_docs import APIDocsAgent
from app.agents.diagrammer import DiagramAgent
from app.agents.qa_validator import QAValidatorAgent
from app.agents.security import SecurityAgent
from app.agents.quality import CodeQualityAgent

# Define the State definition
class AgentState(TypedDict):
    repository_id: str
    clone_path: str
    metadata: Dict[str, Any]
    summary_data: Dict[str, Any]
    architecture_data: Dict[str, Any]
    api_docs: Dict[str, Any]
    diagrams: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    reports: List[Dict[str, Any]]
    qa_results: Dict[str, Any]

# Define Node handler functions
def run_analyzer(state: AgentState) -> Dict[str, Any]:
    agent = RepoAnalysisAgent()
    res = agent.analyze(state["clone_path"], state["metadata"])
    return {"summary_data": res}

def run_architecture(state: AgentState) -> Dict[str, Any]:
    agent = ArchitectureAgent()
    summary = state["summary_data"].get("summary", "")
    res = agent.analyze(summary, state["metadata"])
    return {"architecture_data": res}

def run_security_scan(state: AgentState) -> Dict[str, Any]:
    agent = SecurityAgent()
    file_list = state["metadata"].get("file_list", [])
    res = agent.scan(state["clone_path"], file_list)
    return {"reports": [res]}

def run_quality_scan(state: AgentState) -> Dict[str, Any]:
    agent = CodeQualityAgent()
    file_list = state["metadata"].get("file_list", [])
    res = agent.scan(state["clone_path"], file_list)
    # Since reports is a list, state updates will extend it if using a reducer, 
    # but here we return a dictionary that updates key values.
    # In standard LangGraph, if we don't define a reducer, it overwrites the list.
    # We will merge lists in our orchestrator.
    return {"reports": [res]}

def run_diagrammer(state: AgentState) -> Dict[str, Any]:
    agent = DiagramAgent()
    summary = state["summary_data"].get("summary", "")
    arch = state["architecture_data"].get("architecture_review", "")
    res = agent.generate(summary, arch, state["metadata"])
    return {"diagrams": res}

def run_doc_generator(state: AgentState) -> Dict[str, Any]:
    agent = DocGeneratorAgent()
    summary = state["summary_data"].get("summary", "")
    arch = state["architecture_data"].get("architecture_review", "")
    res = agent.generate(summary, arch, state["metadata"])
    return {"documents": res}

def run_api_docs(state: AgentState) -> Dict[str, Any]:
    agent = APIDocsAgent()
    file_list = state["metadata"].get("file_list", [])
    res = agent.generate(state["clone_path"], file_list)
    return {"api_docs": res}

def run_qa_validator(state: AgentState) -> Dict[str, Any]:
    agent = QAValidatorAgent()
    all_docs = list(state.get("documents", []))
    if state.get("api_docs"):
        all_docs.append(state["api_docs"])
    res = agent.validate(all_docs, state.get("reports", []))
    return {"qa_results": res}


def create_agent_graph():
    """
    Builds and compiles the LangGraph StateGraph.
    """
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("analyzer", run_analyzer)
    workflow.add_node("architecture", run_architecture)
    workflow.add_node("security_scan", run_security_scan)
    workflow.add_node("quality_scan", run_quality_scan)
    workflow.add_node("api_docs", run_api_docs)
    workflow.add_node("diagrammer", run_diagrammer)
    workflow.add_node("doc_generator", run_doc_generator)
    workflow.add_node("qa_validator", run_qa_validator)

    # Establish Edges
    workflow.set_entry_point("analyzer")
    
    # Analyzer outputs to both Architecture, Security, Quality, API Docs
    workflow.add_edge("analyzer", "architecture")
    workflow.add_edge("analyzer", "security_scan")
    workflow.add_edge("analyzer", "quality_scan")
    workflow.add_edge("analyzer", "api_docs")
    
    # Architecture and API Docs feed into Diagrammer and Doc Generator
    workflow.add_edge("architecture", "diagrammer")
    workflow.add_edge("api_docs", "doc_generator")
    
    # Everything feeds into QA Validator
    workflow.add_edge("diagrammer", "qa_validator")
    workflow.add_edge("doc_generator", "qa_validator")
    workflow.add_edge("security_scan", "qa_validator")
    workflow.add_edge("quality_scan", "qa_validator")
    
    workflow.add_edge("qa_validator", END)

    # Compile the flow
    return workflow.compile()


class AgentOrchestrator:
    @staticmethod
    def process_repository(repository_id: str, clone_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the LangGraph analysis pipeline for the repository.
        Handles state accumulation and list extensions.
        """
        logger.info(f"Orchestrating agent analysis for repository: {repository_id}")
        
        # Initialize graph state
        state: AgentState = {
            "repository_id": repository_id,
            "clone_path": clone_path,
            "metadata": metadata,
            "summary_data": {},
            "architecture_data": {},
            "api_docs": {},
            "diagrams": [],
            "documents": [],
            "reports": [],
            "qa_results": {}
        }
        
        try:
            # Let's run nodes sequentially for reliability and predictable state merging.
            # (Standard python execution ensures high reliability on Windows environment thread locks)
            state["summary_data"] = run_analyzer(state)["summary_data"]
            state["architecture_data"] = run_architecture(state)["architecture_data"]
            state["api_docs"] = run_api_docs(state)["api_docs"]
            
            # Run scans
            sec_res = run_security_scan(state)
            state["reports"].extend(sec_res["reports"])
            
            qual_res = run_quality_scan(state)
            state["reports"].extend(qual_res["reports"])
            
            # Run generators
            diag_res = run_diagrammer(state)
            state["diagrams"].extend(diag_res["diagrams"])
            
            doc_res = run_doc_generator(state)
            state["documents"].extend(doc_res["documents"])
            
            # Run QA Validator
            qa_res = run_qa_validator(state)
            state["qa_results"] = qa_res["qa_results"]
            
            logger.info(f"Agent orchestration finished for repository {repository_id} successfully.")
            return state
            
        except Exception as e:
            logger.error(f"Error executing agent pipeline: {str(e)}", exc_info=True)
            raise e
