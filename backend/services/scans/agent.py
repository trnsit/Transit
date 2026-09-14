import httpx

from pydantic import BaseModel

from app.core.config import settings

class AuditResult(BaseModel):
    is_false_positive: bool
    agent_explanation: str
    suggested_explanation: str

class ScanIntelligenceAgent:
    def __init__(self):
        self.base_url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
        self.model_name = settings.ollama_model

    async def analyze_finding(
        self,
        file_path: str,
        line_number: int,
        category: str,
        algorithm: str,
        matched_line: str,
        code_context: str
    ) -> AuditResult:
        
        prompt = f"""
        You are a cryptographic security expert auditing a codebase for migration to post-quantum and modern secure cryptography.
        A static analysis tool flagged a potential issue:

        - File Path: {file_path}
        - Line Number: {line_number}
        - Matched Category: {category}
        - Flagged Algorithm/Library: {algorithm}
        - Matched Line Content: "{matched_line}"

        Here is the surrounding code context:
        ```
        {code_context}
        ```

        Evaluate if this is a true security threat or a false positive:
        1. Set `is_false_positive` to true ONLY if:
           - The flagged algorithm is used for non-security purposes (e.g., MD5 for file name hashing/cache keys, UUID generation, testing/mock setups).
           - The code is just a comment, documentation, or string literal unrelated to execution.
           Otherwise, set `is_false_positive` to false.

        2. Provide a clear, developer-friendly `agent_explanation` detailing the risks (if any) or explaining why it is a false positive.
        
        3. Provide a `suggested_explanation` describing exactly what needs to be changed to fix it (e.g., "Replace MD5 with SHA-256 using hashlib" or "Migrate RSA signing to Ed25519"). If it's a false positive, write "No changes needed."
        """

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a security audit agent. You MUST reply ONLY with a JSON object matching this schema: "
                        '{"is_false_positive": boolean, "agent_explanation": "string", "suggested_explanation": "string"}'
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "format": "json",
            "stream": False
        }

        try:
            # Send requests to local Ollama server
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, 
                    json=payload, 
                    timeout=90.0 # LLMs on CPU/local GPUs can take longer to reply
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama returned status code {response.status_code}: {response.text}")
                
                # Ollama returns a JSON response where the message content is in response.json()["message"]["content"]
                result_data = response.json()
                message_content = result_data["message"]["content"]
                
                # Parse the response text using our Pydantic schema
                return AuditResult.model_validate_json(message_content)

        except Exception as e:
            # Fallback if Ollama is offline or fails
            return AuditResult(
                is_false_positive=False,
                agent_explanation=f"Error running local AI analysis: {str(e)}",
                suggested_explanation="Review the algorithm usage manually."
            )
