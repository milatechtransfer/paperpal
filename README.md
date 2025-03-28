# paperpal

MCP Extension to aid you in searching and writing literature reviews

## Quickstart

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