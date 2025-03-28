# paperpal

MCP Extension to aid you in searching and writing literature reviews

## What it can do

`paperpal` gives your LLMs access to [arxiv](https://www.arxiv.org) and semantic search of papers on [Hugging Face papers](https://huggingface.co/papers)

Here's an example conversation digging more about KV Cache techniques:
    https://claude.ai/share/49a14959-ca5f-4382-a00a-83030ffd081d

## Quickstart

There are many different ways with which you can interact with an MCP server.

### Claude Desktop App

> If this is your first time using an MCP server for Claude Desktop App, see https://modelcontextprotocol.io/quickstart/user

First, clone this repository locally:

    git clone https://github.com/jerpint/paperpal

Next, add the extension to your app. Open your configuration file (on macOS this should be `~/Library/Application Support/Claude/claude_desktop_config.json`) and and add the following to the extension:

For example on MacOS:

```python
{
  "mcpServers": {
    "paperpal": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/<username>/paperpal",
        "run",
        "paperpal.py"
      ]
    }
  }
}
```

Restart your Claude Desktop App and you should see it appear.


### Cursor

TODO

### Overleaf

TODO