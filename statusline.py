#!/usr/bin/env python3
"""
Claude Code Status Line
Reads JSON from stdin and outputs a formatted single-line status display
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class Config:
    """Load and manage configuration"""

    DEFAULT_CONFIG = {
        "colors": True,
        "icons": {
            "clean": "✅",
            "dirty": "🚧",
            "ahead": "⇡",
            "behind": "⇣",
            "high_usage": "⚠️"
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config = self.DEFAULT_CONFIG.copy()

        if config_path is None:
            script_dir = Path(__file__).parent
            config_path = script_dir / 'config.json'

        if Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
            except (json.JSONDecodeError, IOError):
                pass

    def _merge_config(self, user_config: Dict[str, Any]):
        """Recursively merge user config with defaults"""
        def merge(base, override):
            for key, value in override.items():
                if isinstance(value, dict) and key in base:
                    merge(base[key], value)
                else:
                    base[key] = value
        merge(self.config, user_config)

    def get(self, *keys):
        """Get nested config value"""
        value = self.config
        for key in keys:
            value = value.get(key, {})
        return value


class TranscriptParser:
    """Parse Claude Code transcript file to extract session metrics"""

    def __init__(self, transcript_path: Optional[str] = None):
        self.transcript_path = transcript_path
        self.metrics = {
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'assistant_message_count': 0,
            'session_start_time': None,
        }

        if transcript_path and Path(transcript_path).exists():
            self._parse()

    def _parse(self):
        """Parse the transcript file and extract metrics"""
        try:
            with open(self.transcript_path, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        self._process_entry(entry)
                    except json.JSONDecodeError:
                        continue
        except (IOError, OSError):
            pass

    def _process_entry(self, entry: Dict[str, Any]):
        """Process a single transcript entry"""
        entry_type = entry.get('type')
        timestamp = entry.get('timestamp')

        if timestamp and not self.metrics['session_start_time']:
            self.metrics['session_start_time'] = timestamp

        if entry_type == 'assistant':
            self.metrics['assistant_message_count'] += 1
            message = entry.get('message', {})
            usage = message.get('usage', {})
            self.metrics['total_input_tokens'] += usage.get('input_tokens', 0)
            self.metrics['total_output_tokens'] += usage.get('output_tokens', 0)

    def get(self, key: str, default=None):
        """Get a metric value"""
        return self.metrics.get(key, default)


class GitInfo:
    """Extract git repository information"""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir

    def get_branch(self) -> Optional[str]:
        """Get current git branch name"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def is_dirty(self) -> bool:
        """Check if working directory has uncommitted changes"""
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=1
            )
            return bool(result.stdout.strip()) if result.returncode == 0 else False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_remote_status(self) -> tuple[int, int]:
        """Get commits ahead/behind remote (returns ahead, behind)"""
        try:
            result = subprocess.run(
                ['git', 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) == 2:
                    return int(parts[0]), int(parts[1])
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        return 0, 0


class StatusLine:
    """Format and display Claude Code status information"""

    # ANSI color codes
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    CYAN = '\033[36m'
    MAGENTA = '\033[35m'

    def __init__(self, data: Dict[str, Any], config: Config, transcript: Optional[TranscriptParser] = None):
        self.data = data
        self.config = config
        self.transcript = transcript
        self.use_color = config.get('colors')

    def _c(self, color: str, text: str) -> str:
        """Apply color to text if colors enabled"""
        return f"{color}{text}{self.RESET}" if self.use_color else text

    def _format_workspace(self) -> str:
        """Format workspace/directory name"""
        workspace = self.data.get('workspace', {})
        current_dir = workspace.get('current_dir', '~')
        dir_name = Path(current_dir).name or current_dir
        return self._c(self.BLUE + self.BOLD, dir_name)

    def _format_git_status(self) -> str:
        """Format git branch and status indicators"""
        workspace = self.data.get('workspace', {})
        current_dir = workspace.get('current_dir', '.')

        git = GitInfo(current_dir)
        branch = git.get_branch()

        if not branch:
            return ""

        indicators = []

        # Dirty/clean indicator
        if git.is_dirty():
            icon = self.config.get('icons', 'dirty') or '🚧'
            indicators.append(self._c(self.RED, icon))
        else:
            icon = self.config.get('icons', 'clean') or '✅'
            indicators.append(self._c(self.GREEN, icon))

        # Remote tracking
        ahead, behind = git.get_remote_status()
        if ahead > 0:
            icon = self.config.get('icons', 'ahead') or '⇡'
            indicators.append(self._c(self.CYAN, f'{icon}{ahead}'))
        if behind > 0:
            icon = self.config.get('icons', 'behind') or '⇣'
            indicators.append(self._c(self.YELLOW, f'{icon}{behind}'))

        status_str = ''.join(indicators)
        branch_colored = self._c(self.MAGENTA, branch)

        return f"{branch_colored}{status_str}"

    def _format_model(self) -> str:
        """Format model name"""
        model = self.data.get('model', {})
        display_name = model.get('display_name', 'Unknown')
        return self._c(self.CYAN, display_name)

    def _format_tokens(self) -> str:
        """Format token usage"""
        if not self.transcript:
            return ""

        total_tokens = (
            self.transcript.get('total_input_tokens', 0) +
            self.transcript.get('total_output_tokens', 0)
        )

        if total_tokens == 0:
            return ""

        # Model context limits
        model_id = self.data.get('model', {}).get('id', '')
        context_limit = 1000000 if '1m' in model_id.lower() else 200000

        tokens_pct = (total_tokens / context_limit) * 100
        color = self.GREEN if tokens_pct < 50 else (self.YELLOW if tokens_pct < 80 else self.RED)

        # Format token count
        if total_tokens >= 1000:
            token_str = f"{total_tokens/1000:.0f}k"
        else:
            token_str = str(total_tokens)

        # Add warning emoji if usage is high
        warning = ""
        if tokens_pct > 60:
            icon = self.config.get('icons', 'high_usage') or '⚠️'
            warning = self._c(self.YELLOW, icon)

        return f"{self._c(self.DIM, 'tokens:')} {self._c(color, f'{tokens_pct:.0f}%')} ({token_str}){warning}"

    def _format_session(self) -> str:
        """Format session duration"""
        if not self.transcript:
            return ""

        start_time = self.transcript.get('session_start_time')
        if not start_time:
            return ""

        try:
            start_time_clean = start_time.replace('Z', '+00:00')
            start = datetime.fromisoformat(start_time_clean)
            if start.tzinfo:
                start = start.replace(tzinfo=None)
            duration = datetime.now() - start
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)

            if hours > 0:
                time_str = f"{hours}h{minutes}m"
            else:
                time_str = f"{minutes}m"

            return f"{self._c(self.DIM, 'session:')} {self._c(self.CYAN, time_str)}"
        except (ValueError, AttributeError):
            return ""

    def _format_response_time(self) -> str:
        """Format average API response time"""
        cost = self.data.get('cost', {})
        total_api_ms = cost.get('total_api_duration_ms', 0)
        msg_count = self.transcript.get('assistant_message_count', 0) if self.transcript else 0

        if total_api_ms == 0 or msg_count == 0:
            return ""

        avg_ms = total_api_ms // msg_count

        # Color based on response time
        if avg_ms < 5000:
            color = self.CYAN
        elif avg_ms < 10000:
            color = self.YELLOW
        else:
            color = self.RED

        return f"{self._c(self.DIM, 'response:')} {self._c(color, f'{avg_ms}ms')}"

    def format(self) -> str:
        """Generate the single-line status display"""
        parts = [
            self._format_workspace(),
            self._format_git_status(),
            self._format_model(),
            self._format_tokens(),
            self._format_session(),
            self._format_response_time(),
        ]

        # Filter out empty parts
        return ' | '.join(p for p in parts if p)


def main():
    """Main entry point"""
    try:
        data = json.load(sys.stdin)
        config = Config()

        # Parse transcript file for detailed metrics
        transcript_path = data.get('transcript_path')
        transcript = TranscriptParser(transcript_path) if transcript_path else None

        # Generate and print status line
        statusline = StatusLine(data, config, transcript)
        print(statusline.format())

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
