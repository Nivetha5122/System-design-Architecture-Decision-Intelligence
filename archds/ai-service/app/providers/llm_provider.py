from abc import ABC,abstractmethod
import os,httpx
class LLMProvider(ABC):
 @abstractmethod
 def enrich(self,system:str,payload:dict)->dict: ...
class DeterministicProvider(LLMProvider):
 def enrich(self,system,payload): return {"mode":"deterministic","note":"Deterministic architecture reasoning used because no external LLM was configured."}
class OpenAICompatibleProvider(LLMProvider):
 def __init__(self): self.key=os.getenv("LLM_API_KEY","");self.base=os.getenv("LLM_BASE_URL","https://api.openai.com/v1");self.model=os.getenv("LLM_MODEL","gpt-4o-mini")
 def enrich(self,system,payload):
  if not self.key:return DeterministicProvider().enrich(system,payload)
  try:
   r=httpx.post(self.base.rstrip("/")+"/chat/completions",headers={"Authorization":f"Bearer {self.key}"},json={"model":self.model,"messages":[{"role":"system","content":system},{"role":"user","content":str(payload)}],"temperature":0},timeout=25)
   r.raise_for_status();return {"mode":"llm","content":r.json()["choices"][0]["message"]["content"]}
  except Exception:return DeterministicProvider().enrich(system,payload)
def provider(): return OpenAICompatibleProvider() if os.getenv("LLM_API_KEY") else DeterministicProvider()
