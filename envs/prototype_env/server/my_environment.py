import asyncio
from dataclasses import dataclass
from typing import Optional
from playwright.async_api import async_playwright

@dataclass
class MyEnvV4Action:
    message: str

@dataclass
class MyEnvV4Observation:
    echoed_message: str

@dataclass
class MyEnvV4Result:
    observation: MyEnvV4Observation
    reward: float
    done: bool

class MyEnvV4Env:
    """
    A Browser-Based version of the MyEnvV4 environment using Playwright.
    """
    def __init__(self, max_steps: int = 8):
        self.step_count = 0
        self.max_steps = max_steps
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Scenario data
        self.target_url = "https://example.com"

    @classmethod
    async def from_docker_image(cls, image_name: Optional[str] = None):
        return cls()

    async def reset(self) -> MyEnvV4Result:
        self.step_count = 0
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
        
        self.page = await self.browser.new_page()
        
        init_msg = "Browser Environment Initialized. Use GOTO: <url> to navigate."
        return MyEnvV4Result(
            observation=MyEnvV4Observation(echoed_message=init_msg),
            reward=0.0,
            done=False
        )

    async def step(self, action: MyEnvV4Action) -> MyEnvV4Result:
        self.step_count += 1
        msg = action.message.strip().strip('"').strip("'").strip()
        
        reward = 0.0
        response_text = ""
        done = self.step_count >= self.max_steps

        try:
            if msg.startswith("GOTO:"):
                url = msg.replace("GOTO:", "").strip()
                await self.page.goto(url)
                content = await self.page.content()
                # Simplified observation: Just the body text
                response_text = f"URL: {url}\nPage Content: {content[:500]}..."
                reward = 1.0
            
            elif msg.startswith("CLICK:"):
                selector = msg.replace("CLICK:", "").strip()
                await self.page.click(selector)
                content = await self.page.content()
                response_text = f"Clicked {selector}.\nNew Content: {content[:500]}..."
                reward = 1.0
                
            elif msg.startswith("FINAL:"):
                answer = msg.replace("FINAL:", "").strip()
                # Mock success condition for example.com
                if "Example Domain" in answer:
                    response_text = "SUCCESS: Found correct domain info."
                    reward = 10.0
                    done = True
                else:
                    response_text = "FAILURE: Incorrect information provided."
                    reward = -2.0
            else:
                response_text = f"REJECTED: '{msg}' is not a valid browser command. Use GOTO: or CLICK:."
                reward = 0.0
        except Exception as e:
            response_text = f"BROWSER ERROR: {str(e)}"
            reward = -1.0

        return MyEnvV4Result(
            observation=MyEnvV4Observation(echoed_message=response_text),
            reward=reward,
            done=done
        )

    async def close(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
