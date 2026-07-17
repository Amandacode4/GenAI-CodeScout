# Week 1 Submission

## What I Learnt

From this task I learnt a bit more about how chat based AI apps work. One thing I found interesting was that the API itself doesn't remember previous msgs, so the conversation history has to be stored and sent again each time. I also got some practice working with API keys and environment variables.

## Decisions I Made

I kept everything inside a ChatAgent class. It made the code easier to manage since message history, model calls, reset functionality and compaction were all in one place instead of being spread across the file , added multiple model options at the start , reason flexibility ,,then  used a list to store all messages exchanged during the chat it allows the model to keep track of previous context and respond more naturally....Instead of removing old msgs completely, I chose to summarise them  when the chat history gets too large this was a better option because some important context is still kept while reducing the number of tokens being sent.
The API key is inside a .env file for safety.

## Special Requirement

As mentioned in the instructions, I decoded the base64 value from the README and added:

self._buffer_throttle_limit = 42

inside the ChatAgent class.
