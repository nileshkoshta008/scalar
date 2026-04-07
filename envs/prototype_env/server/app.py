from fastapi import FastAPI, HTTPException
import uvicorn
import asyncio
from typing import Optional

# Import our standardized environment and models
from ..models import MyEnvAction, MyEnvObservation
from .my_environment import MyEnvV4Env

app = FastAPI()

# Global environment instance
env = MyEnvV4Env()

@app.post("/reset")
async def reset():
    """
    Mandatory endpoint for OpenEnv validation.
    Resets the browser and environment session.
    """
    try:
        result = await env.reset()
        return {
            "observation": result.observation.echoed_message,
            "reward": result.reward,
            "done": result.done
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(action: MyEnvAction):
    """
    Standard endpoint for taking a step.
    Expects a JSON body matching MyEnvAction.
    """
    try:
        result = await env.step(action)
        return {
            "observation": result.observation.echoed_message,
            "reward": result.reward,
            "done": result.done
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Standard setup for OpenEnv / HF Spaces
    uvicorn.run(app, host="0.0.0.0", port=7860)
