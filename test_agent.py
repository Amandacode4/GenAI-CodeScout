import os
from dotenv import load_dotenv
from chatbot import ChatAgent

load_dotenv()
agent = ChatAgent(model="google/gemma-4-31b-it:free", max_turns=2)
agent.add_user_message("Hello! This is a test. Please reply with 'Testing 123'")
agent.call_model(stream=False)
