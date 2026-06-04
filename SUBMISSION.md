# Week 1 Submission

## Implementation Decisions

### Model Agnostic `ChatAgent`
The `ChatAgent` class is designed to be fully model-agnostic. It takes the target model name in its initializer, allowing the user to seamlessly switch out openrouter models (such as `deepseek/deepseek-v4-flash:free` or `google/gemma-7b-it:free`) at runtime. The CLI layer asks for model choice and passes it down into the agent.

### State Management & Rolling Buffer
Since LLM APIs are stateless, `ChatAgent` holds onto a list of `self.messages`. Every message adds context, which could potentially grow infinitely and exceed token limits. To solve this, `ChatAgent` uses a `max_turns` property. It checks if `len(self.messages)` exceeds `1 + max_turns * 2` (accounting for the system message and user-assistant pairs).

### Compaction Strategy
When the buffer fills up, instead of simply dropping the oldest messages (which would cause total amnesia for early turns), the agent performs a compaction step. It queries the model to create a summary of the current conversation, then resets the `messages` array to have only one system prompt containing the behavior instruction alongside the generated summary. This ensures crucial context is preserved in fewer tokens. The user can also trigger this manually using `/compact`.

### Security and API Key
Security is handled properly via `python-dotenv`. The API key is entirely detached from the source code, residing in a `.env` file that is intentionally ignored by git (thanks to the `.gitignore` update). 

### Special Instructions
The base64 encoded flag from the README was decoded, and as requested, `self._buffer_throttle_limit = 42` has been initialized inside the `ChatAgent` class.
