#!/usr/bin/env python3
"""
Test script to preview statusline output with sample data
"""

import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Create a mock transcript file with sample session data
def create_mock_transcript():
    """Create a temporary transcript file with realistic test data"""
    transcript_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)

    # Session started 2 hours 37 minutes ago
    session_start = datetime.now() - timedelta(hours=2, minutes=37)

    # Simulate 10 exchanges (20 messages total)
    for i in range(10):
        msg_time = session_start + timedelta(minutes=i * 15)

        # User message
        user_msg = {
            "type": "user",
            "uuid": f"user-{i}",
            "timestamp": msg_time.isoformat() + "Z",
            "message": {"role": "user", "content": "test message"}
        }
        transcript_file.write(json.dumps(user_msg) + '\n')

        # Assistant message with token usage
        assistant_msg = {
            "type": "assistant",
            "uuid": f"assistant-{i}",
            "timestamp": (msg_time + timedelta(seconds=30)).isoformat() + "Z",
            "message": {
                "role": "assistant",
                "usage": {
                    "input_tokens": 15000 + (i * 1000),
                    "output_tokens": 2000 + (i * 200),
                    "cache_creation_input_tokens": 5000 if i == 0 else 0,
                    "cache_read_input_tokens": 50000 + (i * 5000)
                }
            }
        }
        transcript_file.write(json.dumps(assistant_msg) + '\n')

    transcript_file.close()
    return transcript_file.name

# Create mock transcript
transcript_path = create_mock_transcript()

# Sample data matching actual Claude Code JSON structure
sample_data = {
    "session_id": "test-session-123",
    "transcript_path": transcript_path,
    "cwd": "/home/jmw/wsl_code/github/williajm/claude-statusline",
    "model": {
        "id": "claude-sonnet-4-5-20250929[1m]",
        "display_name": "Sonnet 4.5 (1M context)"
    },
    "workspace": {
        "current_dir": "/home/jmw/wsl_code/github/williajm/claude-statusline",
        "project_dir": "/home/jmw/wsl_code/github/williajm/claude-statusline"
    },
    "version": "2.0.49",
    "output_style": {
        "name": "default"
    },
    "cost": {
        "total_cost_usd": 0.15,
        "total_duration_ms": 150000,
        "total_api_duration_ms": 25000,
        "total_lines_added": 120,
        "total_lines_removed": 45
    },
    "exceeds_200k_tokens": False
}

# Run the statusline script
result = subprocess.run(
    ['python3', 'statusline.py'],
    input=json.dumps(sample_data),
    text=True,
    capture_output=True
)

print("Sample Output:")
print("=" * 80)
print(result.stdout)
print("=" * 80)

if result.stderr:
    print("\nErrors:", result.stderr)

# Clean up mock transcript file
Path(transcript_path).unlink(missing_ok=True)
