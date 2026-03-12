"""
AMP Command Line Interface

Usage:
    amp init                        Initialize AMP in current directory
    amp agent create <name> <role>  Create a new agent
    amp agent list                  List all agents
    amp agent info <name>           Show agent details
    amp agent forget <name>         Delete an agent's data

    amp memory search <query>       Search agent memories
    amp memory stats                Show memory statistics
    amp memory consolidate          Run memory consolidation

    amp run <config>                Run agents from config file
    amp status                      Show AMP system status
    amp version                     Show version

Examples:
    amp init
    amp agent create Ali project_manager --lang zh
    amp agent list
    amp memory search "deployment steps"
    amp run config/agents.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from amp import __version__
from amp.agent import Agent
from amp.memory import MemoryType

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Colors for terminal output
# ──────────────────────────────────────────────

class Colors:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"

    @staticmethod
    def supports_color() -> bool:
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def c(text: str, color: str) -> str:
    """Colorize text if terminal supports it."""
    if Colors.supports_color():
        return f"{color}{text}{Colors.RESET}"
    return text


# ──────────────────────────────────────────────
# Banner
# ──────────────────────────────────────────────

BANNER = """
  =========================================
  | AMP - Agent Memory Protocol           |
  | Amplifying Intelligence Through Memory |
  =========================================
"""


def print_banner():
    print(c(BANNER, Colors.CYAN))


# ──────────────────────────────────────────────
# AMP Home Directory
# ──────────────────────────────────────────────

def get_amp_home() -> Path:
    """Get AMP home directory (~/.amp)."""
    home = Path.home() / ".amp"
    home.mkdir(parents=True, exist_ok=True)
    return home


def get_agents_dir() -> Path:
    """Get agents storage directory."""
    d = get_amp_home() / "agents"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ──────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────

def cmd_version(args):
    """Show version."""
    print(f"AMP (Agent Memory Protocol) v{__version__}")


def cmd_status(args):
    """Show AMP system status."""
    print_banner()

    amp_home = get_amp_home()
    agents_dir = get_agents_dir()

    # Count agents
    agent_files = list(agents_dir.glob("*.json"))
    agent_count = len(agent_files)

    # Count memories
    memory_count = 0
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir():
            memories_dir = agent_dir / "memories"
            if memories_dir.exists():
                memory_count += len(list(memories_dir.glob("*.json")))

    print(f"  {c('AMP Home:', Colors.BOLD)}      {amp_home}")
    print(f"  {c('Agents:', Colors.BOLD)}        {agent_count}")
    print(f"  {c('Total Memories:', Colors.BOLD)} {memory_count}")
    print(f"  {c('Version:', Colors.BOLD)}       {__version__}")
    print()

    if agent_count > 0:
        print(f"  {c('Registered Agents:', Colors.BOLD)}")
        for f in agent_files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                name = data.get("name", "unknown")
                role = data.get("role", "unknown")
                level = data.get("level", 1)
                xp = data.get("experience_points", 0)
                print(
                    f"    • {c(name, Colors.GREEN)} "
                    f"({role}) "
                    f"Lv.{level} "
                    f"[{xp} XP]"
                )
            except Exception:
                pass
        print()


def cmd_init(args):
    """Initialize AMP in current directory."""
    print_banner()

    amp_home = get_amp_home()
    config_dir = Path.cwd() / ".amp"

    if config_dir.exists():
        print(f"  {c('⚠️  AMP already initialized in this directory', Colors.YELLOW)}")
        return

    config_dir.mkdir(parents=True, exist_ok=True)

    # Create local config
    config_content = {
        "project": {
            "name": Path.cwd().name,
            "description": "",
        },
        "agents": [],
        "settings": {
            "storage_dir": str(amp_home / "agents"),
            "log_level": "INFO",
        },
    }

    config_path = config_dir / "config.json"
    config_path.write_text(
        json.dumps(config_content, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"  {c('✅ AMP initialized!', Colors.GREEN)}")
    print(f"  Config: {config_path}")
    print()
    print("  Next steps:")
    print(f"    {c('amp agent create Ali project_manager', Colors.CYAN)}")
    print(f"    {c('amp agent list', Colors.CYAN)}")


def cmd_agent_create(args):
    """Create a new agent."""
    name = args.name
    role = args.role
    lang = getattr(args, "lang", "en")

    print(f"\n  Creating agent '{c(name, Colors.GREEN)}' ({role})...")

    agent = Agent(
        name=name,
        role=role,
        language=lang,
        capabilities=getattr(args, "skills", "").split(",") if getattr(args, "skills", "") else [],
    )

    print(f"  {c('Agent created!', Colors.GREEN)}")
    print(f"  ID:    {agent.identity.agent_id}")
    print(f"  Name:  {agent.identity.name}")
    print(f"  Role:  {agent.identity.role}")
    print(f"  Level: {agent.identity.level}")
    print(f"  Store: {agent._storage_dir}")
    print()


def cmd_agent_list(args):
    """List all agents."""
    agents_dir = get_agents_dir()
    agent_files = list(agents_dir.glob("*.json"))

    if not agent_files:
        print(f"\n  {c('No agents found.', Colors.DIM)}")
        print(f"  Create one: {c('amp agent create <name> <role>', Colors.CYAN)}")
        print()
        return

    print(f"\n  {c('AMP Agents', Colors.BOLD)}")
    print(f"  {'─' * 56}")
    print(
        f"  {c('Name', Colors.BOLD):<20} "
        f"{c('Role', Colors.BOLD):<18} "
        f"{c('Lvl', Colors.BOLD):>5} "
        f"{c('XP', Colors.BOLD):>7} "
        f"{c('Tasks', Colors.BOLD):>7}"
    )
    print(f"  {'─' * 56}")

    for f in sorted(agent_files):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            name = data.get("name", "?")
            role = data.get("role", "?")
            level = data.get("level", 1)
            xp = data.get("experience_points", 0)
            tasks = data.get("tasks_completed", 0)
            print(f"  {name:<20} {role:<18} {level:>5} {xp:>7} {tasks:>7}")
        except Exception:
            pass

    print(f"  {'─' * 56}")
    print(f"  Total: {len(agent_files)} agents")
    print()


def cmd_agent_info(args):
    """Show agent details."""
    name = args.name
    agents_dir = get_agents_dir()

    # Find agent file
    agent_file = None
    agent_id = None
    for f in agents_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("name", "").lower() == name.lower():
                agent_file = f
                agent_id = data.get("agent_id")
                break
        except Exception:
            pass

    if agent_file is None:
        print(f"\n  {c(f'Agent \"{name}\" not found.', Colors.RED)}")
        return

    data = json.loads(agent_file.read_text(encoding="utf-8"))

    print(f"\n  {c('Agent Details', Colors.BOLD)}")
    print(f"  {'─' * 40}")
    print(f"  Name:       {c(data.get('name', '?'), Colors.GREEN)}")
    print(f"  Role:       {data.get('role', '?')}")
    print(f"  ID:         {data.get('agent_id', '?')}")
    print(f"  Version:    {data.get('version', '?')}")
    print(f"  Created:    {data.get('created_at', '?')}")
    print(f"  Level:      {data.get('level', 1)}")
    print(f"  XP:         {data.get('experience_points', 0)}")
    print(f"  Tasks Done: {data.get('tasks_completed', 0)}")
    print(f"  Tasks Fail: {data.get('tasks_failed', 0)}")
    print(f"  Success:    {data.get('success_rate', 0):.1%}")
    print(f"  Skills:     {', '.join(data.get('capabilities', []))}")

    personality = data.get("personality", {})
    if personality:
        print(f"  Style:      {personality.get('style', '?')}")

    # Count memories
    if agent_id:
        mem_dir = agents_dir / agent_id / "memories"
        if mem_dir.exists():
            mem_count = len(list(mem_dir.glob("*.json")))
            print(f"  Memories:   {mem_count}")

    print(f"  {'─' * 40}")
    print()


def cmd_agent_forget(args):
    """Delete an agent's data."""
    import shutil

    name = args.name
    agents_dir = get_agents_dir()

    # Find agent
    agent_file = None
    agent_id = None
    for f in agents_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("name", "").lower() == name.lower():
                agent_file = f
                agent_id = data.get("agent_id")
                break
        except Exception:
            pass

    if agent_file is None:
        print(f"\n  {c(f'Agent \"{name}\" not found.', Colors.RED)}")
        return

    confirm = input(
        f"\n  Are you sure you want to delete agent "
        f"'{c(name, Colors.RED)}' and all memories? [y/N] "
    )

    if confirm.lower() != "y":
        print("  Cancelled.")
        return

    # Delete files
    agent_file.unlink()
    if agent_id:
        agent_data_dir = agents_dir / agent_id
        if agent_data_dir.exists():
            shutil.rmtree(agent_data_dir)

    print(f"  {c(f'✅ Agent \"{name}\" deleted.', Colors.GREEN)}")
    print()


def cmd_memory_search(args):
    """Search agent memories."""
    query = args.query
    agent_name = getattr(args, "agent", None)
    limit = getattr(args, "limit", 10)

    agents_dir = get_agents_dir()

    async def _search():
        results = []

        # Search through all agent memories
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            if agent_name and agent_dir.name.lower() != agent_name.lower():
                continue

            memories_dir = agent_dir / "memories"
            if not memories_dir.exists():
                continue

            for mem_file in memories_dir.glob("*.json"):
                try:
                    data = json.loads(mem_file.read_text(encoding="utf-8"))
                    content = data.get("content", "").lower()
                    tags = " ".join(data.get("tags", [])).lower()

                    if query.lower() in content or query.lower() in tags:
                        results.append(data)
                except Exception:
                    pass

        return results

    results = asyncio.run(_search())

    # Sort by importance
    results.sort(key=lambda x: x.get("importance", 0), reverse=True)
    results = results[:limit]

    if not results:
        print(f"\n  {c('No memories found.', Colors.DIM)}")
        return

    type_icons = {
        "episodic": "📅",
        "semantic": "📚",
        "procedural": "🔧",
        "emotional": "💡",
    }

    print(f"\n  {c(f'Search Results for \"{query}\"', Colors.BOLD)} ({len(results)} found)")
    print(f"  {'─' * 60}")

    for r in results:
        icon = type_icons.get(r.get("type", ""), "📝")
        content = r.get("content", "")
        if len(content) > 70:
            content = content[:68] + ".."
        imp = r.get("importance", 0)
        strength = r.get("strength", 0)
        emotion = r.get("emotion", "neutral")

        emotion_icon = ""
        if emotion == "positive":
            emotion_icon = " ✅"
        elif emotion == "negative":
            emotion_icon = " ⚠️"

        print(
            f"  {icon} [{r.get('type', '?'):<10}] "
            f"{content}{emotion_icon}"
        )
        print(
            f"     imp={imp} str={strength:.2f} "
            f"tags={r.get('tags', [])}"
        )
        print()


def cmd_memory_stats(args):
    """Show memory statistics."""
    agents_dir = get_agents_dir()

    total = 0
    by_type = {}
    by_emotion = {}
    by_agent = {}

    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue

        agent_name = agent_dir.name
        memories_dir = agent_dir / "memories"
        if not memories_dir.exists():
            continue

        agent_count = 0
        for mem_file in memories_dir.glob("*.json"):
            try:
                data = json.loads(mem_file.read_text(encoding="utf-8"))
                mtype = data.get("type", "unknown")
                emotion = data.get("emotion", "neutral")

                by_type[mtype] = by_type.get(mtype, 0) + 1
                by_emotion[emotion] = by_emotion.get(emotion, 0) + 1
                agent_count += 1
                total += 1
            except Exception:
                pass

        if agent_count > 0:
            by_agent[agent_name[:16]] = agent_count

    print(f"\n  {c('Memory Statistics', Colors.BOLD)}")
    print(f"  {'─' * 40}")
    print(f"  Total memories: {c(str(total), Colors.GREEN)}")
    print()

    if by_type:
        print(f"  {c('By Type:', Colors.BOLD)}")
        type_icons = {
            "episodic": "📅",
            "semantic": "📚",
            "procedural": "🔧",
            "emotional": "💡",
        }
        for t, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            icon = type_icons.get(t, "📝")
            bar = "█" * min(count, 30)
            print(f"    {icon} {t:<12} {count:>4}  {c(bar, Colors.BLUE)}")
        print()

    if by_emotion:
        print(f"  {c('By Emotion:', Colors.BOLD)}")
        emotion_icons = {"positive": "✅", "negative": "⚠️", "neutral": "➖"}
        for e, count in sorted(by_emotion.items(), key=lambda x: x[1], reverse=True):
            icon = emotion_icons.get(e, "❓")
            print(f"    {icon} {e:<12} {count:>4}")
        print()

    if by_agent:
        print(f"  {c('By Agent:', Colors.BOLD)}")
        for agent, count in sorted(by_agent.items(), key=lambda x: x[1], reverse=True):
            print(f"    🤖 {agent:<16} {count:>4}")
        print()


def cmd_memory_consolidate(args):
    """Run memory consolidation for all agents."""

    async def _consolidate():
        agents_dir = get_agents_dir()
        total_stats = {
            "promoted": 0,
            "decayed": 0,
            "merged": 0,
            "patterns_found": 0,
        }

        for agent_file in agents_dir.glob("*.json"):
            try:
                data = json.loads(agent_file.read_text(encoding="utf-8"))
                name = data.get("name", "?")
                role = data.get("role", "?")

                agent = Agent(
                    name=name,
                    role=role,
                    storage_dir=str(agents_dir),
                )
                stats = await agent.sleep()

                for k in total_stats:
                    total_stats[k] += stats.get(k, 0)

                print(
                    f"  💤 {name}: "
                    f"promoted={stats['promoted']}, "
                    f"decayed={stats['decayed']}, "
                    f"patterns={stats['patterns_found']}"
                )
            except Exception as e:
                logger.debug(f"Skip agent {agent_file}: {e}")

        print(f"\n  {c('Consolidation Summary:', Colors.BOLD)}")
        print(f"    Promoted:  {total_stats['promoted']}")
        print(f"    Decayed:   {total_stats['decayed']}")
        print(f"    Merged:    {total_stats['merged']}")
        print(f"    Patterns:  {total_stats['patterns_found']}")

    print(f"\n  {c('Running memory consolidation...', Colors.BOLD)}")
    asyncio.run(_consolidate())
    print()


# ──────────────────────────────────────────────
# Argument Parser
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="amp",
        description="AMP — Agent Memory Protocol CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Every AI deserves to remember. ⚡",
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show version",
    )

    subparsers = parser.add_subparsers(dest="command")

    # init
    subparsers.add_parser("init", help="Initialize AMP in current directory")

    # status
    subparsers.add_parser("status", help="Show AMP system status")

    # version
    subparsers.add_parser("version", help="Show version")

    # agent
    agent_parser = subparsers.add_parser("agent", help="Agent management")
    agent_sub = agent_parser.add_subparsers(dest="agent_command")

    # agent create
    create_p = agent_sub.add_parser("create", help="Create a new agent")
    create_p.add_argument("name", help="Agent name")
    create_p.add_argument("role", help="Agent role")
    create_p.add_argument("--lang", default="zh", help="Language (default: zh)")
    create_p.add_argument("--skills", default="", help="Comma-separated skills")

    # agent list
    agent_sub.add_parser("list", help="List all agents")

    # agent info
    info_p = agent_sub.add_parser("info", help="Show agent details")
    info_p.add_argument("name", help="Agent name")

    # agent forget
    forget_p = agent_sub.add_parser("forget", help="Delete agent data")
    forget_p.add_argument("name", help="Agent name")

    # memory
    memory_parser = subparsers.add_parser("memory", help="Memory management")
    memory_sub = memory_parser.add_subparsers(dest="memory_command")

    # memory search
    search_p = memory_sub.add_parser("search", help="Search memories")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--agent", help="Filter by agent")
    search_p.add_argument("--limit", type=int, default=10, help="Max results")

    # memory stats
    memory_sub.add_parser("stats", help="Show memory statistics")

    # memory consolidate
    memory_sub.add_parser("consolidate", help="Run memory consolidation")

    return parser


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        cmd_version(args)
        return

    command = getattr(args, "command", None)

    if command is None:
        print_banner()
        parser.print_help()
        return

    commands = {
        "init": cmd_init,
        "status": cmd_status,
        "version": cmd_version,
    }

    if command in commands:
        commands[command](args)
    elif command == "agent":
        agent_commands = {
            "create": cmd_agent_create,
            "list": cmd_agent_list,
            "info": cmd_agent_info,
            "forget": cmd_agent_forget,
        }
        sub = getattr(args, "agent_command", None)
        if sub in agent_commands:
            agent_commands[sub](args)
        else:
            print(f"\n  Usage: amp agent {{create|list|info|forget}}")
    elif command == "memory":
        memory_commands = {
            "search": cmd_memory_search,
            "stats": cmd_memory_stats,
            "consolidate": cmd_memory_consolidate,
        }
        sub = getattr(args, "memory_command", None)
        if sub in memory_commands:
            memory_commands[sub](args)
        else:
            print(f"\n  Usage: amp memory {{search|stats|consolidate}}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
