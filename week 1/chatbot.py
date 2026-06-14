import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

if "OPENROUTER_API_KEY" not in os.environ or os.environ["OPENROUTER_API_KEY"] == "your_api_key_here":
    print("Please set your OPENROUTER_API_KEY in the .env file.")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

class ChatAgent:
    def __init__(self, model="google/gemma-4-31b-it:free", max_turns=10):
        self.model = model
        self.max_turns = max_turns
        self._buffer_throttle_limit = 42
        self.messages = [
            {"role": "system", "content": "You are a helpful and intelligent assistant."}
        ]

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self.check_compaction()

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def reset(self):
        self.messages = [
            {"role": "system", "content": "You are a helpful and intelligent assistant."}
        ]
        print("--- History Reset ---")

    def compact_history(self):
        # compress old chat into summary
        if len(self.messages) <= 3:
            print("--- History too short to compact ---")
            return
            
        print("--- Compacting History ---")
        compaction_prompt = "Please summarize the conversation so far in a concise manner, capturing all key facts, names, preferences, and important context."
        temp_messages = self.messages + [{"role": "user", "content": compaction_prompt}]
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=temp_messages,
            )
            summary = response.choices[0].message.content
            
            # keep only summary
            self.messages = [
                {"role": "system", "content": f"You are a helpful and intelligent assistant.\nHere is a summary of the conversation so far:\n{summary}"}
            ]
            print("--- History Compacted ---")
        except Exception as e:
            print(f"Error during compaction: {e}")

    def check_compaction(self):
        # max_turns is in pairs (user+assistant), plus the system message.
        # len(messages) grows by 2 every turn.
        # Limit len to 1 + (max_turns * 2)
        if len(self.messages) > 1 + (self.max_turns * 2):
            self.compact_history()

    def call_model(self, stream=True):
        # call model and stream reply
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=stream
            )
            
            full_reply = ""
            if stream:
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            print(content, end="", flush=True)
                            full_reply += content
                print() # newline after streaming
            else:
                full_reply = response.choices[0].message.content
                print(full_reply)
            
            self.add_assistant_message(full_reply)
            
        except Exception as e:
            print(f"Error calling model: {e}")

def run_chatbot():
    print("Available models:")
    models = [
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "moonshotai/kimi-k2.6:free"
    ]
    for i, model in enumerate(models):
        print(f"{i+1}. {model}")
    
    choice = input("Select a model [1]: ").strip()
    selected_model = models[0]
    if choice.isdigit() and 1 <= int(choice) <= len(models):
        selected_model = models[int(choice)-1]
    
    print(f"\nUsing model: {selected_model}")
    agent = ChatAgent(model=selected_model, max_turns=5)
    
    print("\nChat started. Commands: /exit, /reset, /compact")
    print("-------------------------------------------------")
    
    while True:
        try:
            user_input = input("\n[YOU] ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ['/exit', 'exit', 'quit']:
                print("Goodbye!")
                break
            elif user_input.lower() == '/reset':
                agent.reset()
                continue
            elif user_input.lower() == '/compact':
                agent.compact_history()
                continue
                
            agent.add_user_message(user_input)
            print("[MODEL] ", end="", flush=True)
            agent.call_model(stream=True)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    run_chatbot()
