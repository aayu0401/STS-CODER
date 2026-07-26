"""
STS Coder — Standalone Z-Command CLI Lookup Tool
================================================
Run Z-Command explanations directly from terminal without Ollama.

Usage:
  python zcmd.py list
  python zcmd.py ZDSYS
  python zcmd.py ZDECB
"""

import sys
import os

# Add backend directory to module search path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from llm.tpf_knowledge import ZCMD_RESPONSES, format_zcmd_explanation, parse_zcmd_verb, KNOWLEDGE

def lookup_zcmd(cmd_input: str):
    if not cmd_input or cmd_input.lower() == "list":
        print("\n" + "=" * 60)
        print("  STS Coder — Built-in Z-Commands Repository")
        print("=" * 60)
        for cmd, info in sorted(ZCMD_RESPONSES.items()):
            print(f"  • {cmd:<10} [{info['category']:<15}] — {info['purpose']}")
        print("=" * 60)
        print("\nUsage: python zcmd.py <COMMAND>  (e.g., python zcmd.py ZDSYS)\n")
        return

    base_cmd = parse_zcmd_verb(cmd_input)
    detail = ZCMD_RESPONSES.get(base_cmd)
    if detail:
        print("\n" + format_zcmd_explanation(cmd_input, detail) + "\n")
    else:
        kb_desc = KNOWLEDGE.get("z_commands", {}).get(base_cmd)
        if kb_desc:
            print(f"\n**Command:** {base_cmd}\n**Purpose:** {kb_desc}\n")
        else:
            print(f"\nUnknown Z-Command '{cmd_input}'. Run `python zcmd.py list` to view available commands.\n")

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "list"
    lookup_zcmd(query)
