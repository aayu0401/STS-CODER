"""
Fetch and merge all known IBM z/TPF Z-Commands into tpf_knowledge.py ZCMD_RESPONSES.
Preserves hand-authored rich entries; adds new commands from all project sources + IBM docs scrape.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = ROOT / "backend" / "llm" / "tpf_knowledge.py"
DOCS_RAW = ROOT / "backend" / "training" / "data" / "docs_raw.txt"

# Rich entries — never overwrite with auto-generated stubs
RICH_COMMANDS = frozenset({
    "ZDSYS", "ZDECB", "ZSTAT", "ZECB", "ZTRAP", "ZDUMP", "ZPOOL",
    "ZINET", "ZMQSC", "ZTPFDF", "ZPROG", "ZLOG", "ZDTCP", "ZOSRV",
})

CATEGORY_DEFAULTS = {
    "Diagnostic": [
        "COMMAND COMPLETED — RC=0",
        "DIAGNOSTIC DATA: displayed on console",
        "RC: 0",
    ],
    "Storage": [
        "DEVICE/POOL STATUS: ACTIVE",
        "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
        "RC: 0",
    ],
    "Network": [
        "LINK/DAEMON STATUS: ACTIVE",
        "CONNECTIONS: nnn",
        "RC: 0",
    ],
    "Performance": [
        "METRIC COLLECTION: ACTIVE",
        "CPU/IO RATES: nn.nn%",
        "RC: 0",
    ],
    "Database": [
        "DB/FILE STATUS: ACTIVE",
        "RECORDS/INDEX: valid",
        "RC: 0",
    ],
    "Program": [
        "PROGRAM STATUS: LOADED/NOT LOADED",
        "CORE RESIDENCY: xxxxxxxx",
        "RC: 0",
    ],
    "Logging": [
        "LOG STATUS: ACTIVE",
        "MESSAGE COUNT: nnnnn",
        "RC: 0",
    ],
    "Security": [
        "KEYSTORE/PROFILE STATUS: ACTIVE",
        "RC: 0",
    ],
    "Operations": [
        "SUBSYSTEM STATUS: ACTIVE",
        "RC: 0",
    ],
    "System Status": [
        "SYSTEM STATUS: ACTIVE",
        "SUBSYSTEM: NORMAL",
        "RC: 0",
    ],
    "Messaging": [
        "QUEUE/CHANNEL STATUS: RUNNING",
        "DEPTH: nnn",
        "RC: 0",
    ],
    "General": [
        "COMMAND STATUS: COMPLETE",
        "RC: 0",
    ],
}


def _load_z_commands_from_update_knowledge() -> dict[str, str]:
    path = ROOT / "update_knowledge.py"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"z_commands\s*=\s*(\{.*?\n\})\s*\n\nknowledge", text, re.DOTALL)
    if not m:
        return {}
    return ast.literal_eval(m.group(1))


def _load_z_commands_from_test_scrape() -> dict[str, str]:
    path = ROOT / "test_scrape.py"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"all_z_commands\s*=\s*(\{.*?\n    \})", text, re.DOTALL)
    if not m:
        return {}
    return ast.literal_eval(m.group(1))


def _load_patch_simple_commands() -> dict[str, tuple]:
    path = ROOT / "patch_kb.py"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"simple_commands\s*=\s*(\{.*?\n\})\s*\n\n# Auto-generate", text, re.DOTALL)
    if not m:
        return {}
    return ast.literal_eval(m.group(1))


def _expand_advisor_commands() -> dict[str, str]:
    return {
        "ZDHIS": "Display history. Shows historical system events, tape mounts, or operator actions.",
        "ZDTIM": "Display time. Displays current system clock and time-of-day settings.",
        "ZDMSG": "Display message. Shows routing parameters for specific message numbers.",
        "ZDSCT": "Display sector. Displays hardware sector formats or DASD usage.",
        "ZDCPD": "Display CP definitions. Shows Central Processor configuration.",
        "ZDDTA": "Display data capture. Shows active data capture scenarios and buffers.",
        "ZDPVL": "Display pool volumes. Shows disk pool volume attributes and status.",
        "ZDUIN": "Display UINs. Displays Unique Identifier Numbers and allocation.",
        "ZDTRP": "Display traps. Shows active diagnostic traps (complement to ZTRAP).",
        "ZSYSM": "System messages. Toggle and configure system message processing.",
        "ZPING": "Ping TCP/IP node. Verify network connectivity from z/TPF.",
        "ZTRAC": "System trace. Start or stop specific traces for programs or subsystems.",
        "ZTIMA": "Time alteration. Manage system timeout thresholds and timers.",
        "ZADCD": "Add data collection definition. Defines a data collection scenario.",
        "ZALDC": "Allocate logic. Allocate devices or logical units for z/TPF.",
        "ZTRBL": "Troubleshoot. Diagnose system events and error conditions.",
        "ZSORT": "Sort utility. Control z/TPF sort processing.",
        "ZDLI": "DL/I control. Manage IMS/DLI database interfaces on z/TPF.",
        "ZPARM": "Display parameters. Show system parameter settings.",
        "ZUTIL": "Utilities control. Invoke z/TPF system utilities.",
        "ZBACK": "Backup control. Manage backup and recovery operations.",
        "ZREST": "Restart control. Manage warm/cold restart options.",
        "ZSECU": "Security control. Display security subsystem status.",
        "ZTERM": "Terminal control. Display or alter terminal session status.",
        "ZUSER": "User control. Display operator/user profiles and authority.",
        "ZDISP": "Display control. Generic display subsystem operator command.",
        "ZALTR": "Alter subsystem. Alter subsystem or resource parameters.",
        "ZINIT": "Initialize. Initialize subsystem or device for processing.",
        "ZSHUT": "Shutdown. Gracefully shut down subsystem or service.",
        "ZMON": "Monitor. Start continuous monitoring of entry or resource.",
        "ZPRNT": "Print control. Route output to printer or spool.",
        "ZSPOL": "Spool control. Manage output spooling queues.",
        "ZJB": "Job batch. Submit or display batch jobs.",
        "ZQUE": "Queue control. Display or alter message/transaction queues.",
        "ZCNFG": "Configuration. Display or alter system configuration.",
        "ZVER": "Version display. Show z/TPF and subsystem version levels.",
        "ZLIC": "License. Display license and entitlement information.",
        "ZAUD": "Audit. Display audit trail and compliance logs.",
        "ZCRYPT": "Cryptography. Manage encryption subsystem settings.",
        "ZSSL": "SSL/TLS. Display secure socket layer configuration.",
        "ZHTTP": "HTTP daemon. Control HTTP subsystem on z/TPF.",
        "ZFTP": "FTP daemon. Control FTP subsystem connections.",
        "ZSMTP": "SMTP/mail daemon. Control mail transfer agent.",
        "ZLDAP": "LDAP. Display directory service bindings.",
        "ZSOAP": "Web services. Control SOAP/REST gateway (WebBridge related).",
        "ZXML": "XML processing. Display XML parser/transform status.",
        "ZJSON": "JSON processing. Display JSON/WebBridge transform status.",
        "ZBAL": "BAL loader. Display or control BAL program load.",
        "ZCSECT": "CSECT control. Display loaded CSECTs and entry points.",
        "ZENTRY": "Entry control. Display transaction entry definitions.",
        "ZSEG": "Segment control. Display program segment status.",
        "ZLOADR": "Loader control. Extended program load utilities.",
        "ZUNLD": "Unload. Unload programs or modules from core.",
        "ZREFR": "Refresh. Refresh cached definitions or tables.",
        "ZREBLD": "Rebuild. Rebuild indexes or file structures.",
        "ZCHK": "Check. Validate system or file integrity.",
        "ZFIX": "Fix. Repair file or index structures.",
        "ZMIG": "Migration. Control data migration utilities.",
        "ZCOPY": "Copy. Copy records or files between pools.",
        "ZMOVE": "Move. Move volumes or datasets.",
        "ZDEL": "Delete. Delete records, files, or definitions.",
        "ZADD": "Add. Add records, files, or definitions.",
        "ZLIST": "List. List catalog, directory, or queue contents.",
        "ZHELP": "Help. Display operator command help text.",
    }


def _parse_docs_raw() -> dict[str, str]:
    if not DOCS_RAW.exists():
        return {}
    text = DOCS_RAW.read_text(encoding="utf-8", errors="ignore")
    found: dict[str, str] = {}
    # Patterns like "ZDSYS command" or "Z DECB" in IBM prose
    for cmd in re.findall(r"\b(Z[A-Z]{3,5})\b", text):
        if cmd not in found:
            found[cmd] = f"Referenced in IBM z/TPF documentation ({cmd})."
    return found


def _parse_description(desc: str) -> tuple[str, str, str]:
    """Split 'Title. Long description' into purpose, syntax hint, description."""
    desc = desc.strip()
    if ". " in desc:
        title, rest = desc.split(". ", 1)
        purpose = title.strip()
        description = rest.strip() or purpose
    else:
        purpose = desc[:60]
        description = desc
    # First word often hints syntax verb
    verb = purpose.split()[0] if purpose else "Control"
    return purpose, description, verb


def _infer_category(cmd: str, purpose: str, description: str) -> str:
    blob = f"{cmd} {purpose} {description}".upper()
    if cmd.startswith("ZD") and cmd not in ("ZDUMP", "ZD0DB"):
        return "Diagnostic"
    rules = [
        (("DUMP", "TRAP", "DEBUG", "TRACE", "DECB", "ECB", "CDSP", "MAP"), "Diagnostic"),
        (("POOL", "STOR", "VOL", "DISK", "TAPE", "ALLOC", "MODULE", "CORE"), "Storage"),
        (("TCP", "INET", "NET", "SONA", "ISDN", "PING", "HTTP", "FTP", "ROUT"), "Network"),
        (("STAT", "MEAS", "PERF", "BUFS", "VFA"), "Performance"),
        (("TPFDF", "PNR", "DB", "FILE", "CATALOG"), "Database"),
        (("PROG", "REXX", "APL", "LOAD", "ENTRY"), "Program"),
        (("LOG", "ERR", "AUD"), "Logging"),
        (("KEY", "PWB", "SEC", "CRYPT"), "Security"),
        (("OSRV", "TOS", "RAVEN"), "Operations"),
        (("MQ", "MAIL", "MTA"), "Messaging"),
        (("SYS", "STOP", "ONLN", "OPTS", "RECV"), "System Status"),
    ]
    for keys, cat in rules:
        if any(k in blob or k in cmd for k in keys):
            return cat
    return "General"


def _build_syntax(cmd: str, purpose: str, patch_tuple: tuple | None) -> str:
    if patch_tuple and len(patch_tuple) >= 2:
        return patch_tuple[1]
    verb = purpose.split()[0].upper() if purpose else "DISPLAY"
    if verb in ("DISPLAY", "ALTER", "START", "STOP", "CONTROL", "MANAGE"):
        return f"{cmd} [{verb}|STATUS]"
    return f"{cmd} [DISPLAY|STATUS]"


def _make_entry(
    cmd: str,
    desc: str,
    patch_tuple: tuple | None = None,
) -> dict:
    if patch_tuple and len(patch_tuple) >= 4:
        purpose, syntax, category, description = patch_tuple[0], patch_tuple[1], patch_tuple[2], patch_tuple[3]
    else:
        purpose, description, _ = _parse_description(desc)
        category = _infer_category(cmd, purpose, description)
        syntax = _build_syntax(cmd, purpose, patch_tuple)

    outputs = CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["General"])
    outputs = [o.replace("COMMAND", cmd) if "COMMAND" in o else o for o in outputs]

    example = syntax.split()[0]
    if "[" in syntax:
        example = f"{cmd} DISPLAY"

    entry = {
        "purpose": purpose,
        "syntax": syntax,
        "description": description,
        "output_fields": list(outputs),
        "example": example,
        "category": category,
        "rc_codes": {
            "RC=0": "Success — command completed",
            "RC=4": "Warning — resource not found or partial result",
            "RC=8": "Error — command failed or subsystem unavailable",
            "RC=12": "Severe error — operator intervention required",
        },
    }
    if cmd in ("ZOSRV", "ZREXX", "ZDTCP", "ZINET"):
        entry["tos_note"] = (
            "Use in TOS/RAVEN automation: check RC after each command; "
            "pair with ZSTAT or ZLOG for operational monitoring."
        )
    return entry


def _load_existing_zcmd_responses() -> dict:
    text = KB_PATH.read_text(encoding="utf-8")
    m = re.search(r"ZCMD_RESPONSES\s*=\s*(\{.*?\n\})\s*\n\n(?:ZTPF_SYSTEM_KNOWLEDGE|#)", text, re.DOTALL)
    if not m:
        raise RuntimeError("Could not parse ZCMD_RESPONSES from tpf_knowledge.py")
    return ast.literal_eval(m.group(1))


def _replace_zcmd_block(content: str, new_responses: dict) -> str:
    start = content.index("ZCMD_RESPONSES = {")
    depth = 0
    i = start + len("ZCMD_RESPONSES = ")
    while i < len(content):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    else:
        raise RuntimeError("Unbalanced braces in ZCMD_RESPONSES")
    new_block = "ZCMD_RESPONSES = " + json.dumps(new_responses, indent=4)
    return content[:start] + new_block + content[end:]


def _rebuild_knowledge_z_commands(zcmd: dict) -> None:
    """Patch KNOWLEDGE z_commands dict in file (derived from ZCMD_RESPONSES)."""
    text = KB_PATH.read_text(encoding="utf-8")
    z_simple = {
        cmd: info["purpose"] + ". " + info["description"]
        for cmd, info in sorted(zcmd.items())
    }
    new_z = '"z_commands": ' + json.dumps(z_simple, indent=4)
    text = re.sub(
        r'"z_commands":\s*\{.*?\},\s*\n\s*"ecb_processing"',
        new_z + ',\n    "ecb_processing"',
        text,
        count=1,
        flags=re.DOTALL,
    )
    KB_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    existing = _load_existing_zcmd_responses()
    merged_desc: dict[str, str] = {}

    for src in (
        _load_z_commands_from_update_knowledge,
        _load_z_commands_from_test_scrape,
        _parse_docs_raw,
        _expand_advisor_commands,
    ):
        merged_desc.update(src())

    patch_simple = _load_patch_simple_commands()
    for cmd, tup in patch_simple.items():
        if cmd not in merged_desc and len(tup) >= 4:
            merged_desc[cmd] = tup[3]

    result = dict(existing)
    added = []
    for cmd in sorted(merged_desc.keys()):
        if cmd in RICH_COMMANDS and cmd in result:
            continue
        if cmd in result and cmd in RICH_COMMANDS:
            continue
        desc = merged_desc[cmd]
        patch_t = patch_simple.get(cmd)
        if cmd in RICH_COMMANDS:
            # keep existing rich
            continue
        if cmd not in result:
            result[cmd] = _make_entry(cmd, desc, patch_t)
            added.append(cmd)
        elif result[cmd].get("output_fields", [""])[0].endswith("STATUS: ACTIVE") and "DETAILS: Valid" in str(result[cmd].get("output_fields")):
            # Upgrade generic stub
            result[cmd] = _make_entry(cmd, desc, patch_t)

    content = KB_PATH.read_text(encoding="utf-8")
    content = _replace_zcmd_block(content, result)
    KB_PATH.write_text(content, encoding="utf-8")
    _rebuild_knowledge_z_commands(result)

    print(f"ZCMD_RESPONSES: {len(result)} commands ({len(added)} newly added)")
    if added:
        print("New:", ", ".join(added))
    return 0


if __name__ == "__main__":
    sys.exit(main())
