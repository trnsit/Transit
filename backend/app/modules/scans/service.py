import os
import re
import ast
import zipfile
import shutil
import tempfile
import httpx
from datetime import datetime
from uuid import UUID
from fastapi import HTTPException, BackgroundTasks

from app.modules.scans.models import Scan
from app.modules.scans.store import ScanStore
from app.modules.repositories.store import RepositoryStore

# Cryptographic rules/regexes for detection and classification
RULES = {
    "POST_QUANTUM": {
        "ML-KEM / Kyber": re.compile(r"\b(kyber|ml-kem)\b", re.IGNORECASE),
        "ML-DSA / Dilithium": re.compile(r"\b(dilithium|ml-dsa)\b", re.IGNORECASE),
        "FN-DSA / Falcon": re.compile(r"\b(falcon|fn-dsa)\b", re.IGNORECASE),
        "SLH-DSA / SPHINCS+": re.compile(r"\b(sphincs|slh-dsa)\b", re.IGNORECASE),
    },
    "QUANTUM_VULNERABLE": {
        "RSA": re.compile(r"\b(rsa|pkcs1|pkcs8|rsassa)\b", re.IGNORECASE),
        "ECDSA": re.compile(r"\b(ecdsa|secp256k1|nistp256|nistp384|prime256v1)\b", re.IGNORECASE),
        "ECDH / DH": re.compile(r"\b(ecdh|diffie-hellman|x25519|curve25519)\b", re.IGNORECASE),
        "EdDSA / Ed25519": re.compile(r"\b(ed25519|eddsa|ed448)\b", re.IGNORECASE),
    },
    "QUANTUM_SAFE_CLASSICAL": {
        "AES-256": re.compile(r"\b(aes[-_]?256|aes|rijndael)\b", re.IGNORECASE),
        "ChaCha20": re.compile(r"\b(chacha20|poly1305)\b", re.IGNORECASE),
        "SHA-256 / SHA-512": re.compile(r"\b(sha256|sha-256|sha512|sha-512)\b", re.IGNORECASE),
        "SHA-3": re.compile(r"\b(sha3|keccak)\b", re.IGNORECASE),
    },
    "CLASSICAL_VULNERABLE": {
        "MD5": re.compile(r"\b(md5)\b", re.IGNORECASE),
        "SHA-1": re.compile(r"\b(sha1|sha-1)\b", re.IGNORECASE),
        "DES / 3DES": re.compile(r"\b(des|3des|triple[-_]?des)\b", re.IGNORECASE),
        "RC4": re.compile(r"\b(rc4|arc4)\b", re.IGNORECASE),
    }
}

# Dynamic Tree-sitter loading configuration
HAS_TREE_SITTER = False
try:
    from tree_sitter import Language, Parser
    import tree_sitter_go as tsgo
    import tree_sitter_javascript as tsjs
    import tree_sitter_java as tsjava
    
    GO_LANG = Language(tsgo.language())
    JS_LANG = Language(tsjs.language())
    JAVA_LANG = Language(tsjava.language())
    
    HAS_TREE_SITTER = True
except Exception:
    pass


class PythonCryptoVisitor(ast.NodeVisitor):
    """AST visitor to extract cryptographic details from Python source files."""
    def __init__(self, file_path: str, lines: list[str]):
        self.file_path = file_path
        self.lines = lines
        self.findings = []
        self.crypto_libs = {"cryptography", "pycryptodome", "Crypto", "hashlib", "ssl"}
        
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split('.')[0] in self.crypto_libs:
                self._add_finding(node.lineno, "Library Import", "General", f"Imported cryptographic library: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] in self.crypto_libs:
            for alias in node.names:
                self._add_finding(node.lineno, "Library Import", "General", f"Imported {alias.name} from {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id

        # Scan function name using our RULES
        for category, algs in RULES.items():
            for alg_name, pattern in algs.items():
                if pattern.findall(func_name):
                    self._add_finding(node.lineno, category, alg_name, f"Called function: {func_name}")
        self.generic_visit(node)

    def visit_Constant(self, node):
        # Match string literals (e.g. algorithms.AES(key))
        if isinstance(node.value, str):
            val = node.value
            for category, algs in RULES.items():
                for alg_name, pattern in algs.items():
                    if pattern.findall(val):
                        self._add_finding(node.lineno, category, alg_name, f"Constant string: '{val}'")

    def _add_finding(self, line_number: int, category: str, algorithm: str, detail: str):
        line_content = self.lines[line_number - 1].strip() if line_number <= len(self.lines) else ""
        self.findings.append({
            "file": self.file_path,
            "line_number": line_number,
            "category": category,
            "algorithm": algorithm,
            "line_content": line_content[:150]
        })


class ScanService:
    def __init__(self, scan_store: ScanStore, repo_store: RepositoryStore):
        self.scan_store = scan_store
        self.repo_store = repo_store
        self.scannable_extensions = {
            ".py", ".js", ".ts", ".go", ".java", ".cpp", ".c", 
            ".rs", ".cs", ".php", ".rb", ".swift", ".kt", ".h"
        }
        self.ignored_dirs = {
            "node_modules", "venv", ".venv", "env", ".git", 
            "__pycache__", "dist", "build", ".github"
        }

    # --- API Core Methods ---
    async def get_scan(self, user_id: UUID, scan_id: UUID) -> Scan:
        scan = await self.scan_store.get_by_id(scan_id, user_id)
        if not scan:
            raise HTTPException(
                status_code=404,
                detail='Scan not found'
            )
        return scan

    async def list_scans(self, user_id: UUID, repository_id: UUID) -> list[Scan]:
        repo = await self.repo_store.get_by_id(user_id, repository_id)
        if not repo:
            raise HTTPException(
                status_code=404,
                detail='Repository not found'
            )
        return await self.scan_store.list_by_repository(repository_id, user_id)

    async def trigger_scan(self, user_id: UUID, repository_id: UUID, background_tasks: BackgroundTasks) -> Scan:
        repo = await self.repo_store.get_by_id(user_id, repository_id)
        if not repo:
            raise HTTPException(
                status_code=404,
                detail='Repository not found'
            )

        token = await self.repo_store.get_github_token(user_id)
        if not token:
            raise HTTPException(
                status_code=400,
                detail='GitHub account not connected. Please connect your GitHub account first.'
            )

        scan = await self.scan_store.create(repository_id)
        background_tasks.add_task(
            self.run_scan_job, 
            scan.id, 
            repo.full_name, 
            token
        )
        return scan

    # --- Job Orchestrator ---

    async def run_scan_job(self, scan_id: UUID, full_name: str, token: str):
        await self.scan_store.update_status(scan_id, 'running')
        
        zip_path = None
        temp_dir = None
        try:
            zip_path = await self.download_github_zip(full_name, token)
            temp_dir = tempfile.mkdtemp()
            self.extract_zip(zip_path, temp_dir)
            
            findings_data = self.scan_directory(temp_dir)
            
            await self.scan_store.save_findings(scan_id, findings_data)
            await self.scan_store.update_status(
                scan_id, 
                'completed', 
                completed_at=datetime.now()
            )
        except Exception as e:
            await self.scan_store.update_status(scan_id, 'failed')
            print(f"Scan {scan_id} failed: {str(e)}")
        finally:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    # --- AST and Parsing Engines ---

    def scan_directory(self, dir_path: str) -> list[dict]:
        results = []
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.scannable_extensions:
                    full_file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_file_path, dir_path)
                    
                    parts = rel_path.split(os.sep)
                    display_path = os.path.join(*parts[1:]) if len(parts) > 1 else rel_path
                    
                    try:
                        with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Eager parsing using specific syntax engines
                            if file_ext == '.py':
                                results.extend(self.scan_python_ast(content, display_path))
                            elif file_ext == '.go' and HAS_TREE_SITTER:
                                results.extend(self.scan_tree_sitter(content, display_path, GO_LANG))
                            elif file_ext in ('.js', '.ts') and HAS_TREE_SITTER:
                                results.extend(self.scan_tree_sitter(content, display_path, JS_LANG))
                            elif file_ext == '.java' and HAS_TREE_SITTER:
                                results.extend(self.scan_tree_sitter(content, display_path, JAVA_LANG))
                            else:
                                results.extend(self.scan_content_regex(content, display_path))
                    except Exception:
                        pass
        return results

    def scan_python_ast(self, content: str, file_path: str) -> list[dict]:
        try:
            tree = ast.parse(content)
            visitor = PythonCryptoVisitor(file_path, content.splitlines())
            visitor.visit(tree)
            return visitor.findings
        except Exception:
            return self.scan_content_regex(content, file_path)

    def scan_tree_sitter(self, content: str, file_path: str, language: Language) -> list[dict]:
        findings = []
        parser = Parser(language)
        tree = parser.parse(bytes(content, "utf8"))
        
        nodes_to_visit = [tree.root_node]
        while nodes_to_visit:
            node = nodes_to_visit.pop()
            
            # Eagerly ignore comments to avoid false-positives
            if "comment" in node.type:
                continue
                
            # Scan text content in leaf nodes (identifiers, strings, function names)
            if not node.children:
                try:
                    node_text = content[node.start_byte:node.end_byte]
                    if node_text:
                        for category, algs in RULES.items():
                            for alg_name, pattern in algs.items():
                                if pattern.findall(node_text):
                                    line_num = node.start_point[0] + 1
                                    lines = content.splitlines()
                                    line_content = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                                    
                                    findings.append({
                                        "file": file_path,
                                        "line_number": line_num,
                                        "category": category,
                                        "algorithm": alg_name,
                                        "line_content": line_content[:150]
                                    })
                except Exception:
                    pass
            
            nodes_to_visit.extend(node.children)
        return findings

    def scan_content_regex(self, content: str, file_path: str) -> list[dict]:
        findings = []
        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for category, algs in RULES.items():
                for alg_name, pattern in algs.items():
                    if pattern.findall(line):
                        findings.append({
                            "file": file_path,
                            "line_number": line_num,
                            "category": category,
                            "algorithm": alg_name,
                            "line_content": line.strip()[:150]
                        })
        return findings

    # --- Zipball Downloads ---
    async def download_github_zip(self, full_name: str, token: str) -> str:
        url = f"https://api.github.com/repos/{full_name}/zipball"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Transit-App"
        }
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to download repository zipball: {response.text}")
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
            temp_file.write(response.content)
            temp_file.close()
            return temp_file.name

    def extract_zip(self, zip_path: str, extract_to: str):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
