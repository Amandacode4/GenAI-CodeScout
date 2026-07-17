import asyncio
from agent import Agent

async def test():
    a = Agent()
    a.messages = [{"role": "system", "content": a._load_system_prompt()}, {"role": "user", "content": "hello"}]
    
    for i, tool in enumerate(a.tools):
        print(f"Testing tool {i}: {tool['function']['name']}")
        try:
            provider = a.providers[0]
            client = provider["client"]
            stream = await client.chat.completions.create(
                model=provider["model"],
                messages=a.messages,
                tools=[tool],
                stream=True,
                temperature=0.3
            )
            async for chunk in stream:
                pass
            print(f"  -> SUCCESS")
        except Exception as e:
            print(f"  -> FAILED: {str(e)[:100]}")
        await asyncio.sleep(4)

asyncio.run(test())
