# claude_statusline

A Python-based status line formatter for Claude Code that displays workspace, git, model, and session information in a clean single-line format.

## Features

Displays all information in a single line separated by ` | `:

```
claude_statusline | feature/branch🚧 | Sonnet 4.5 (1M context) | tokens: 10% (102k) | session: 36m | response: 4275ms
```

**What's shown:**
- **Workspace name** - Current directory name (bold blue)
- **Git branch** - Current branch (magenta) with status:
  - ✅ = clean working directory
  - 🚧 = uncommitted changes
  - ⇡n = commits ahead of remote
  - ⇣n = commits behind remote
- **Model name** - Active Claude model (cyan)
- **Token usage** - Percentage and count (color-coded: green < 50%, yellow < 80%, red ≥ 80%)
  - Shows ⚠️ warning emoji when usage exceeds 60%
- **Session duration** - Time since session started (cyan)
- **Response time** - Average API response time (cyan < 5s, yellow < 10s, red ≥ 10s)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/williajm/claude_statusline.git
cd claude_statusline
```

2. Make the script executable:
```bash
chmod +x statusline.py
```

3. Configure Claude Code to use this statusline. Add to `~/.claude/settings.json`:
```json
{
  "statusLine": {
    "type": "command",
    "command": "/path/to/claude_statusline/statusline.py"
  }
}
```

## Usage

The script reads JSON from stdin (provided by Claude Code) and outputs a formatted single-line status display.

### Testing

Run the included test script to see sample output:

```bash
python3 test_statusline.py
```

## Configuration

Customize via `config.json` in the same directory as `statusline.py`:

```bash
cp config.example.json config.json
# Edit config.json with your preferences
```

### Configuration Options

```json
{
  "colors": true,
  "icons": {
    "clean": "✅",
    "dirty": "🚧",
    "ahead": "⇡",
    "behind": "⇣",
    "high_usage": "⚠️"
  }
}
```

**colors**: Set to `false` to disable ANSI color codes

**icons**: Customize the icons used for:
- `clean` / `dirty` - Git working directory status
- `ahead` / `behind` - Git remote tracking status
- `high_usage` - Token usage warning (shown when > 60%)

## Requirements

- Python 3.7+
- Git (for git status features)
- Standard library only (no external dependencies)

## How It Works

Claude Code provides JSON to the statusline script via stdin with:
- `workspace.current_dir` - Current directory path
- `model.id` and `model.display_name` - Active model information
- `transcript_path` - Path to session transcript file
- `cost.total_api_duration_ms` - API timing information

The script:
1. Parses the transcript file (`.jsonl`) to extract token usage and session metrics
2. Runs git commands to get branch and status information
3. Formats everything into a single colorful line

## License

MIT License - See LICENSE file for details
