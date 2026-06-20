import os
import shutil
from typing import Dict, Any, List, Tuple
from git import Repo, GitCommandError
from app.core.config import settings
from app.core.logging import logger

# Prevent git from prompting for credentials in non-interactive environment
os.environ["GIT_TERMINAL_PROMPT"] = "0"

class IngestionService:
    @staticmethod
    def get_clone_path(repository_id: str) -> str:
        """Returns the local folder path where the repo will be cloned."""
        return os.path.join(settings.REPO_CLONE_DIR, repository_id)

    @classmethod
    def clone_repository(cls, repository_id: str, github_url: str, branch: str = "main") -> str:
        """
        Clones a remote git repository to a local temporary path.
        Configures auth token if provided in settings.
        """
        clone_path = cls.get_clone_path(repository_id)
        
        # Clean up existing folder if it exists
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path, ignore_errors=True)
            
        # Inject auth token if configured
        auth_url = github_url
        if settings.GITHUB_PERSONAL_ACCESS_TOKEN and "github.com" in github_url:
            # Reconstruct URL with PAT token
            # github_url format is typically https://github.com/owner/repo
            token = settings.GITHUB_PERSONAL_ACCESS_TOKEN
            if github_url.startswith("https://"):
                auth_url = github_url.replace("https://", f"https://x-access-token:{token}@")
            elif github_url.startswith("http://"):
                auth_url = github_url.replace("http://", f"http://x-access-token:{token}@")

        logger.info(f"Cloning repository {github_url} (branch: {branch}) to {clone_path}")
        
        try:
            # Clone repo
            Repo.clone_from(auth_url, clone_path, branch=branch, depth=1)
            logger.info(f"Successfully cloned repository {repository_id}")
            return clone_path
        except GitCommandError as e:
            # Handle potential fallback to master branch or fallback cloning
            if "master" in str(e) or "main" in str(e):
                logger.warning(f"Failed to clone branch {branch}, attempting default branch clone...")
                try:
                    if os.path.exists(clone_path):
                        shutil.rmtree(clone_path, ignore_errors=True)
                    Repo.clone_from(auth_url, clone_path, depth=1)
                    logger.info(f"Successfully cloned repository using default branch")
                    return clone_path
                except GitCommandError as inner_e:
                    logger.error(f"Failed default clone as well: {str(inner_e)}")
                    raise inner_e
            logger.error(f"Error cloning repository: {str(e)}")
            raise e

    @classmethod
    def analyze_structure(cls, clone_path: str) -> Dict[str, Any]:
        """
        Scans files, detects programming languages, calculates total LOC and file counts.
        """
        extension_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "React TypeScript",
            ".jsx": "React JavaScript",
            ".go": "Go",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++ Header",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".rs": "Rust",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".html": "HTML",
            ".css": "CSS",
            ".md": "Markdown",
            ".json": "JSON",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".sql": "SQL",
            ".sh": "Shell Script"
        }

        total_files = 0
        total_loc = 0
        language_counts: Dict[str, int] = {}
        language_locs: Dict[str, int] = {}
        file_tree: List[str] = []

        # Ignore common directories
        ignore_dirs = {
            ".git", "node_modules", "venv", ".venv", "env", "dist", 
            "build", "__pycache__", "target", "vendor", ".idea", ".vscode",
            ".pytest_cache", ".mypy_cache", ".tox"
        }

        # Binary and non-source extensions to ignore completely (including ML models/data formats)
        binary_extensions = {
            # Images
            '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp', '.tiff', '.bmp',
            # Documents / PDFs
            '.pdf', '.epub',
            # Archives / Compressed
            '.zip', '.tar', '.gz', '.7z', '.rar', '.bz2',
            # Executables / Libraries
            '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.lib', '.a', '.obj', '.o',
            # Python compiled
            '.pyc', '.pyd', '.pyo',
            # Java compiled
            '.class', '.jar', '.war',
            # Database / storage formats
            '.db', '.sqlite', '.sqlite3',
            # Audio / Video
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.mkv',
            # Fonts
            '.ttf', '.woff', '.woff2', '.eot',
            # Office documents
            '.xlsx', '.docx', '.pptx', '.csv', '.parquet',
            # Machine Learning Models & Serialized Formats (contain NUL bytes/binary data)
            '.pkl', '.pickle', '.npy', '.npz', '.h5', '.hdf5', '.joblib',
            '.model', '.weights', '.pt', '.pth', '.onnx', '.pb',
            '.safetensors', '.feather', '.arrow', '.proto', '.keras'
        }

        for root, dirs, files in os.walk(clone_path):
            # Modify dirs in-place to avoid traversing ignored folders
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, clone_path)
                
                _, ext = os.path.splitext(file)
                ext_lower = ext.lower()
                
                # Append all files to tree and count them so the user sees the complete structure
                file_tree.append(rel_path)
                total_files += 1
                
                # Safeguard 1: Ignore binary/non-code file extensions for language/LOC stats
                if ext_lower in binary_extensions:
                    continue
                    
                # Safeguard 2: Ignore file size > 500 KB for LOC count to avoid OOM and skewing language stats
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 500 * 1024:  # 500 KB
                        continue
                except Exception:
                    continue
                
                lang = extension_map.get(ext_lower, "Other")
                
                language_counts[lang] = language_counts.get(lang, 0) + 1
                
                # Count lines of code safely (skip binary/corrupt files)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        loc = len(lines)
                        total_loc += loc
                        language_locs[lang] = language_locs.get(lang, 0) + loc
                except Exception:
                    pass

        # Calculate percentages
        languages_pct = {}
        if total_loc > 0:
            for lang, loc in language_locs.items():
                languages_pct[lang] = round((loc / total_loc) * 100, 2)

        return {
            "total_files": total_files,
            "total_loc": total_loc,
            "languages": language_counts,
            "languages_loc_percentage": languages_pct,
            "file_list": file_tree[:1000]  # Cap to prevent giant payloads
        }

    @staticmethod
    def cleanup_clone(repository_id: str) -> None:
        """Removes local cloned files to free space."""
        clone_path = os.path.join(settings.REPO_CLONE_DIR, repository_id)
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path, ignore_errors=True)
            logger.info(f"Cleaned up local clone space for repo: {repository_id}")
