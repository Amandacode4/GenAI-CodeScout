import asyncio
from agent import Agent
async def run():
    a = Agent()
    a.messages = [{"role": "system", "content": a._load_system_prompt()}, {"role": "user", "content": "Fix the failing test_appctx.py"}]
    print("Running...")
    try:
        provider = a.providers[0]
        client = provider["client"]
        stream = await client.chat.completions.create(
            model=provider["model"],
            messages=a.messages,
            tools=a.tools,
            stream=True,
            temperature=0.3
        )
        async for chunk in stream:
            print(chunk)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(run())
