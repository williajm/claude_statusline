# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**claude_statusline** is a Python-based custom status line formatter for Claude Code that displays workspace, git, model, and session information in a single colorful line.

The statusline receives JSON from Claude Code via stdin and outputs a formatted single-line display with:
- Workspace name and git branch/status
- Model information
- Token usage percentage (with visual warnings)
- Session duration and response time metrics

## Architecture

### Core Components

**statusline.py** - Main script with four key classes:

1. **Config** (lines 15-60) - Configuration management
   - Loads from `config.json` in script directory
   - Merges user config with defaults
   - Supports customizable icons and color settings

2. **TranscriptParser** (lines 62-108) - Session metrics extraction
   - Parses `.jsonl` transcript file provided by Claude Code
   - Extracts token usage (input/output tokens from `usage` field in assistant messages)
   - Tracks session start time and message counts
   - Critical: Only processes entries with `type: "assistant"` for token metrics

3. **GitInfo** (lines 110-161) - Git repository information
   - Runs git commands in workspace directory
   - Gets current branch, dirty status, and remote tracking (ahead/behind)
   - All git calls have 1-second timeout for safety

4. **StatusLine** (lines 163-330) - Output formatting
   - Combines data from Config, TranscriptParser, and GitInfo
   - Applies ANSI color codes (if enabled)
   - Formats output as single line with ` | ` separators
   - Color-codes metrics based on thresholds (token usage, response time)

### Data Flow

```
Claude Code stdin JSON
  �
main() parses JSON
  �
TranscriptParser reads transcript_path (.jsonl file)
  �
StatusLine combines:
  - Direct JSON fields (model, workspace)
  - Transcript metrics (tokens, session time)
  - Git command output (branch, status)
  �
Single-line formatted output to stdout
```

### Claude Code JSON Structure

Claude Code provides this JSON structure via stdin:
- `transcript_path` - Path to `.jsonl` session transcript (REQUIRED for rich metrics)
- `workspace.current_dir` - Working directory path
- `model.id` and `model.display_name` - Model information
- `cost.total_api_duration_ms` - Total API time for response metrics

The transcript file is the primary source for token usage and session metrics.

## Testing

**test_statusline.py** - Test script that:
- Creates a temporary mock transcript file with realistic session data
- Generates sample JSON matching Claude Code's actual structure
- Runs statusline.py via subprocess with test data
- Verifies output is single-line (Claude Code only displays first line)
- Includes regression test for multi-line output

Run tests:
```bash
python3 test_statusline.py
```

When adding new features that parse transcript data, update the mock transcript generator in `create_mock_transcript()` to include realistic test data.

## Configuration

**config.json** (optional) - User customization:
- `colors: bool` - Enable/disable ANSI color codes
- `icons: object` - Customize status icons (clean/dirty, ahead/behind, high_usage)

Always maintain `config.example.json` as reference documentation for available options.

## Common Development Tasks

**Run the statusline with test data:**
```bash
python3 test_statusline.py
```

**Make executable:**
```bash
chmod +x statusline.py
```

**Test with custom JSON:**
```bash
echo '{"workspace":{"current_dir":"/path"},"model":{"display_name":"Test"}}' | python3 statusline.py
```

## Important Constraints

1. **Single-line output requirement** - Claude Code only displays the first line of stdout. Multi-line output will be truncated.

2. **Transcript parsing is critical** - Without parsing `transcript_path`, the statusline can only show basic info (workspace, git, model). Token usage, session duration, and response time all require transcript parsing.

3. **Git command timeouts** - All git subprocess calls use 1-second timeout to prevent hanging if git is slow or unavailable.

4. **Model context detection** - Context limit (200k vs 1M tokens) is inferred from model ID string containing '1m'.

5. **Error handling philosophy** - The script should never crash. All parsing errors, missing files, and git failures are caught and result in graceful degradation (missing sections in output).

## Session Metrics Implementation

When working with transcript parsing:
- The transcript is a `.jsonl` file with one JSON object per line
- Each line has a `type` field: "user" or "assistant"
- Only "assistant" entries contain `message.usage` with token counts
- Session start time comes from the `timestamp` field of the first entry
- Token fields: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`

## Color Coding Thresholds

Token usage:
- Green: < 50%
- Yellow: 50-80%
- Red: e 80%
- Warning emoji: > 60%

Response time:
- Cyan: < 5s
- Yellow: 5-10s
- Red: e 10s
