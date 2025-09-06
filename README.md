# Lucy
\- a AI assistant


## Features

- [x] Chat
- [x] Multi-step problem solving (agentic)
- [x] Text to Speech
- [x] Speech to Text
- [x] Google Calendar management
- [x] Coder
    - [x] File writing, reading, and deletion
    - [x] Shell access - can execute shell commands
    - [x] Create new tools
    - [x] Run Python code
- [x] Call external MCP tools

## Installation

Export your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

Clone MeloTTS to `./depend/MeloTTS`:

Setup google calendar credentials. 
Expecting a service account token at `./tokens/calendar.json`

Download requirements through uv
