import httpx
from .models import MyEnvAction, MyEnvObservation

class MyEnvClient:
    """
    A functional HTTP client for the OpenEnv Prototype.
    Communicates with the FastAPI server in envs/prototype_env/server/app.py.
    """
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    async def reset(self) -> MyEnvObservation:
        """Resets the environment via the API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/reset", timeout=30.0)
            response.raise_for_status()
            data = response.json()
            return MyEnvObservation(echoed_message=data["observation"])

    async def step(self, action: MyEnvAction) -> tuple[MyEnvObservation, float, bool]:
        """Performs a step in the environment via the API."""
        async with httpx.AsyncClient() as client:
            # action.dict() or action.model_dump() for serialization
            payload = {"message": action.message}
            response = await client.post(f"{self.base_url}/step", json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            obs = MyEnvObservation(echoed_message=data["observation"])
            return obs, data["reward"], data["done"]
