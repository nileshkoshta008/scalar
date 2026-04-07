import asyncio
import os
import sys
import textwrap
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Import the standardized environment from its new location
from envs.prototype_env import MyEnvAction, Env

# --- Configuration & Environment Variables ---
# Load variables from .env if it exists
load_dotenv()

# Mandatory Configuration Variables (Consolidated at the top)
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
API_KEY = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "prototype_v1")

# Environment Task Variables
TASK_NAME = os.getenv("MY_ENV_V4_TASK", "web_navigation")
BENCHMARK = os.getenv("MY_ENV_V4_BENCHMARK", "prototype_env")

# Execution Parameters
MAX_STEPS = 8
TEMPERATURE = 0.7
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.1  
MAX_TOTAL_REWARD = 11.0 # 1.0 (navigation) + 10.0 (final answer)

# --- Logging Functions (STDOUT Only) ---

def log_start(task: str, env: str, model: str) -> None:
    """Emits the [START] block to stdout."""
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Emits a [STEP] line to stdout."""
    error_val = error if error else "null"
    done_val = str(done).lower()
    clean_action = action.replace("\n", " ").strip()
    print(
        f"[STEP] step={step} action={clean_action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Emits the [END] block to stdout."""
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# --- Helper Functions ---

def get_client_and_model():
    """Detects the provider based on the API key and returns the configured client and model."""
    target_key = API_KEY
    target_url = API_BASE_URL
    target_model = MODEL_NAME

    if target_key:
        if str(target_key).startswith("gsk_"):
            print("[DEBUG] Groq Key detected.", file=sys.stderr)
            target_url = "https://api.groq.com/openai/v1"
            if target_model == "gpt-3.5-turbo":
                target_model = "llama-3.3-70b-versatile"
        elif not str(target_key).startswith("sk-") and HF_TOKEN:
            print("[DEBUG] Hugging Face provider detected.", file=sys.stderr)
            target_url = "https://router.huggingface.co/v1/"
            target_key = HF_TOKEN
            if target_model == "gpt-3.5-turbo":
                target_model = "meta-llama/Llama-3.1-8B-Instruct"
    
    client = OpenAI(base_url=target_url, api_key=target_key or "none")
    return client, target_model

def build_user_prompt(step: int, last_echoed: str, last_reward: float, history: List[str]) -> str:
    """Constructs the prompt for each turn."""
    hist_str = "\n".join(history[-3:]) # Last 3 turns for context
    return textwrap.dedent(
        f"""
        --- Current State ---
        Step: {step}
        Environment Response: '{last_echoed}'
        Last reward: {last_reward:.2f}
        
        --- History ---
        {hist_str}
        
        Provide your next command.
        """
    ).strip()

def get_model_message(client: OpenAI, model: str, step: int, last_echoed: str, last_reward: float, history: List[str]) -> str:
    """Calls the LLM and returns the generated action string."""
    try:
        user_prompt = build_user_prompt(step, last_echoed, last_reward, history)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        # Clean up quotes/whitespace
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()
        return text if text else "hello"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", file=sys.stderr, flush=True)
        return "error_fallback"

# --- System Prompt (Few-Shot) ---

SYSTEM_PROMPT = textwrap.dedent(
    f"""
    You are an AI assistant performing a 'Web Navigation' task using a headless browser.
    You MUST ONLY reply using correctly formatted commands.
    
    ### VALID COMMANDS ###
    1. GOTO: <url>       -> Navigate to a web address.
    2. CLICK: <selector> -> Click on a specific element.
    3. FINAL: <answer>   -> Submit the final answer once found.
    
    ### TASK GOAL ###
    Go to 'https://example.com' and confirm the domain name is 'Example Domain'.
    
    ### SAMPLE INTERACTION ###
    User: --- Current State ---
          Step: 1
          Environment Response: 'Browser Environment Initialized.'
    Assistant: GOTO: https://example.com
    
    User: --- Current State ---
          Step: 2
          Environment Response: 'URL: https://example.com Page Content: ...Example Domain...'
    Assistant: FINAL: Example Domain
    
    ### CRITICAL RULES ###
    - DO NOT use natural language. 
    - ONLY output the command string.
    - If you see the info you need, use FINAL: immediately.
    """
).strip()

# --- Main Logic ---

async def main():
    client, model_to_use = get_client_and_model()
    env = await Env.from_docker_image(LOCAL_IMAGE_NAME)
    
    history = []
    rewards = []
    steps_taken = 0
    score = 0.0
    success = False
    
    log_start(task=TASK_NAME, env=BENCHMARK, model=model_to_use)
    
    try:
        # Initialize
        result = await env.reset()
        last_echoed = result.observation.echoed_message
        last_reward = 0.0
        
        for step in range(1, MAX_STEPS + 1):
            # 1. Get LLM message
            message = get_model_message(client, model_to_use, step, last_echoed, last_reward, history)
            print(f"[DEBUG] Raw Model Output: {message!r}", file=sys.stderr, flush=True)

            # 2. Take step in environment
            result = await env.step(MyEnvAction(message=message))
            obs = result.observation
            reward = result.reward
            done = result.done

            # 3. Log results
            log_step(step=step, action=message, reward=reward, done=done, error=None)
            
            # 4. Update state
            rewards.append(reward)
            steps_taken = step
            last_echoed = obs.echoed_message
            last_reward = reward
            history.append(f"Step {step} Action: {message} Reward: {reward}")
            
            if done:
                break
        
        # Compute final normalized score
        total_reward = sum(rewards)
        score = total_reward / MAX_TOTAL_REWARD
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[ERROR] Main loop failed: {e}", file=sys.stderr)
    finally:
        await env.close()
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    asyncio.run(main())
