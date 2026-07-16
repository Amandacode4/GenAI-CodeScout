import asyncio
from agent import Agent

async def test():
    a = Agent()
    a.messages = [{"role": "system", "content": a._load_system_prompt()}, {"role": "user", "content": "hello"}]
    
    # We know 0-5 are fine. Let's test 6 to 15.
    for i in range(6, len(a.tools)):
        tool = a.tools[i]
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
        await asyncio.sleep(6) # avoid rate limits

asyncio.run(test())
