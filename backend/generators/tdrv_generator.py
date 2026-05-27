"""
STS Coder — TDRV File Generator (RAVEN Format)
=================================================
Generates production-grade IBM z/TPF RAVEN TDRV (Test Driver) files.
Produces proper RAVEN automation format with:
  - Sequential command execution via SEND
  - Response validation with EXPECT / PASS / FAIL
  - Timeout handling via WAIT
  - Retry logic via RETRY / DELAY
  - Recovery processing
  - Wildcard support in EXPECT patterns
  - Pass/fail results summary
"""

from datetime import datetime, timezone
from parser.tpf_parser import ParsedEntry


def _pad(text: str, width: int) -> str:
    """Left-justify text within a fixed-width column."""
    return str(text).ljust(width)


# ═══════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_tdrv_file(entry: ParsedEntry) -> str:
    """Generate complete IBM z/TPF RAVEN TDRV file from ParsedEntry."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = entry.name
    seg = entry.segment
    purpose = entry.purpose or "TPF transaction processing"
    macro_names = {m.name for m in entry.macros}
    lines: list[str] = []

    # ── File Header ──
    lines.append("*" * 72)
    lines.append(f"* TDRV: {name}")
    lines.append(f"* PURPOSE: {purpose}")
    lines.append(f"* Segment:    {seg}")
    lines.append(f"* Generated:  STS Coder | {ts}")
    lines.append("*" * 72)
    lines.append("")

    # Build all test steps
    steps = _build_raven_steps(entry)
    step_count = len(steps)
    pass_count = 0

    for idx, step in enumerate(steps, start=1):
        lines.append(f"* ── Step {idx:02d}/{step_count:02d}: {step['title']} " + "─" * max(1, 50 - len(step['title'])))
        lines.append(f"* {step['comment']}")

        # SEND command
        lines.append(f'SEND "{step["command"]}"')

        # WAIT timeout
        lines.append(f'WAIT {step["timeout"]}')

        # EXPECT patterns (PASS)
        for pattern in step["expect_pass"]:
            lines.append(f'EXPECT "{pattern}" PASS')
            pass_count += 1

        # EXPECT patterns (FAIL)
        for pattern in step["expect_fail"]:
            lines.append(f'EXPECT "{pattern}" FAIL')

        # Retry logic
        if step.get("retry", 0) > 0:
            lines.append(f'RETRY {step["retry"]}')
            lines.append(f'DELAY {step.get("delay", 5)}')

        lines.append("")

    # ── Recovery Section ──
    lines.append(_section_recovery(name, entry))

    # ── Dependency Chain (preserved from original) ──
    lines.append("* ── Dependency Chain ──────────────────────────────────────")
    if entry.dependencies:
        for dep in entry.dependencies:
            lines.append(f"*   → {dep}")
    else:
        lines.append("*   UNKNOWN — Requires TPF validation")
    lines.append("")

    # ── Original Step Table (preserved for backward compat) ──
    lines.append(_original_step_table(entry))

    # ── Results Summary ──
    lines.append("* ── Results Summary ───────────────────────────────────────")
    lines.append(f"* TOTAL STEPS:    {step_count}")
    lines.append(f"* PASS PATTERNS:  {pass_count}")
    lines.append(f"* RECOVERY STEPS: {_count_recovery_steps(entry)}")
    lines.append("*")
    lines.append(f"* EXPECTED RESULT: ALL STEPS PASS")
    lines.append("")
    lines.append("*" * 72)
    lines.append(f"* END OF TDRV — {name}")
    lines.append("*" * 72)

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# STEP BUILDERS
# ═══════════════════════════════════════════════════════════════

def _build_raven_steps(entry: ParsedEntry) -> list[dict]:
    """Build RAVEN TDRV steps based on parsed entry structure."""
    steps = []
    name = entry.name
    macro_names = {m.name for m in entry.macros}

    # Step 1: System readiness check
    steps.append({
        "title": "System Readiness",
        "comment": "Verify TPF Operations Server is active and responsive",
        "command": "ZOSRV STATUS",
        "timeout": 30,
        "expect_pass": ["*OPER*ACTIVE*", "*SERVER*READY*"],
        "expect_fail": ["*OPER*DOWN*", "*SERVER*ERROR*", "*NOT*AVAILABLE*"],
        "retry": 3,
        "delay": 10,
    })

    # Step 2: Entry point initialization
    if macro_names & {"ENTER", "ENTRC", "ENPTS"}:
        enter_macro = next(
            (m for m in entry.macros if m.name in {"ENTER", "ENTRC", "ENPTS"}), None
        )
        enter_detail = f" {enter_macro.operands}" if enter_macro and enter_macro.operands else ""
        steps.append({
            "title": "Entry Initialization",
            "comment": f"Initialize entry point {name} via ENTER macro{enter_detail}",
            "command": f"ZDPRF {name}",
            "timeout": 15,
            "expect_pass": [f"*{name}*LOADED*", f"*{name}*ACTIVE*"],
            "expect_fail": [f"*{name}*NOT*FOUND*", "*LOAD*FAIL*"],
            "retry": 2,
            "delay": 5,
        })

    # Step 3: Input validation
    has_validation = any(i.category == "compare" for i in entry.instructions)
    if has_validation:
        compare_count = sum(1 for i in entry.instructions if i.category == "compare")
        steps.append({
            "title": "Input Validation",
            "comment": f"Validate input data — {compare_count} compare/test instructions detected",
            "command": f"ZDSYS TRACE {name}",
            "timeout": 20,
            "expect_pass": ["*VALID*", "*PASS*", "*OK*"],
            "expect_fail": ["*INVALID*", "*REJECT*", "*BAD*DATA*"],
            "retry": 0,
            "delay": 0,
        })

    # Step 4: File access
    if entry.file_ops:
        file_refs = " ".join(entry.file_ops[:3])
        steps.append({
            "title": "File Access",
            "comment": f"Access TPF file records — refs: {', '.join(entry.file_ops[:5])}",
            "command": f"ZDFIL {entry.file_ops[0]}",
            "timeout": 30,
            "expect_pass": ["*RECORD*FOUND*", f"*{entry.file_ops[0]}*OK*"],
            "expect_fail": ["*RECORD*NOT*FOUND*", "*FILE*ERROR*", "*I/O*ERROR*"],
            "retry": 3,
            "delay": 5,
        })

    # Step 5: PNR processing
    if macro_names & {"PNRCC", "PNRAC"}:
        steps.append({
            "title": "PNR Processing",
            "comment": "Access and process Passenger Name Record",
            "command": f"ZDPNR STATUS",
            "timeout": 30,
            "expect_pass": ["*PNR*ACCESSED*", "*PNR*OK*"],
            "expect_fail": ["*PNR*NOT*FOUND*", "*PNR*LOCKED*", "*PNR*ERROR*"],
            "retry": 2,
            "delay": 5,
        })

    # Step 6: Data processing
    has_data = any(i.category in ("data", "arithmetic") for i in entry.instructions)
    if has_data:
        data_count = sum(1 for i in entry.instructions if i.category in ("data", "arithmetic"))
        steps.append({
            "title": "Data Processing",
            "comment": f"Execute data transformation — {data_count} data/arithmetic operations",
            "command": f"ZDSYS TRACE {name}",
            "timeout": 30,
            "expect_pass": ["*PROCESS*COMPLETE*", "*DATA*OK*"],
            "expect_fail": ["*DATA*ERROR*", "*OVERFLOW*", "*ARITH*ERROR*"],
            "retry": 0,
            "delay": 0,
        })

    # Step 7: Service calls
    if macro_names & {"SERVC", "SVCRC"}:
        steps.append({
            "title": "Service Call",
            "comment": "Execute TPF service call and validate response",
            "command": f"ZOSRV {name}",
            "timeout": 60,
            "expect_pass": ["*SERVICE*OK*", "*SVC*COMPLETE*"],
            "expect_fail": ["*SERVICE*FAIL*", "*SVC*ERROR*", "*TIMEOUT*"],
            "retry": 3,
            "delay": 10,
        })

    # Step 8: Storage management
    if macro_names & {"GETCC", "RELCC", "GETFC", "RELFC", "ALASC", "RLASC"}:
        steps.append({
            "title": "Storage Management",
            "comment": "Verify storage allocation and release integrity",
            "command": f"ZDSYS POOL STATUS",
            "timeout": 15,
            "expect_pass": ["*POOL*OK*", "*STORAGE*RELEASED*"],
            "expect_fail": ["*POOL*EXHAUSTED*", "*STORAGE*LEAK*"],
            "retry": 0,
            "delay": 0,
        })

    # Step 9: ECB verification
    if entry.ecb_refs:
        steps.append({
            "title": "ECB Verification",
            "comment": f"Verify ECB state — refs: {', '.join(entry.ecb_refs[:4])}",
            "command": f"ZDECB {entry.ecb_refs[0]}",
            "timeout": 15,
            "expect_pass": ["*ECB*ACTIVE*", "*ECB*OK*"],
            "expect_fail": ["*ECB*DEADLOCK*", "*ECB*ERROR*"],
            "retry": 0,
            "delay": 0,
        })

    # Step 10: Error handling validation
    if entry.error_points:
        steps.append({
            "title": "Error Handling",
            "comment": f"Validate error paths — {len(entry.error_points)} error points",
            "command": f"ZDSYS TRACE {name} ERRORS",
            "timeout": 20,
            "expect_pass": ["*ERROR*HANDLED*", "*RECOVERY*OK*"],
            "expect_fail": ["*UNHANDLED*", "*ABEND*"],
            "retry": 0,
            "delay": 0,
        })

    # Step 11: Communication
    if macro_names & {"SENDC", "SENDM"}:
        steps.append({
            "title": "Message Send",
            "comment": "Validate outbound message transmission",
            "command": f"ZDSYS MSG {name}",
            "timeout": 20,
            "expect_pass": ["*MSG*SENT*", "*SEND*OK*"],
            "expect_fail": ["*MSG*FAIL*", "*SEND*ERROR*"],
            "retry": 2,
            "delay": 5,
        })

    # Final: Exit verification
    has_exit = bool(macro_names & {"EXITC", "EXITN", "BACKC", "BACK"})
    if has_exit:
        exit_type = "EXITC/EXITN" if macro_names & {"EXITC", "EXITN"} else "BACKC/BACK"
        steps.append({
            "title": "Exit Verification",
            "comment": f"Verify clean exit via {exit_type}",
            "command": f"ZDPRF {name}",
            "timeout": 15,
            "expect_pass": [f"*{name}*COMPLETE*", "*EXIT*OK*", "*RC=0*"],
            "expect_fail": ["*ABEND*", "*ABNORMAL*", "*RC=12*"],
            "retry": 0,
            "delay": 0,
        })
    else:
        steps.append({
            "title": "Completion Check",
            "comment": "Verify entry completed processing",
            "command": f"ZDPRF {name}",
            "timeout": 15,
            "expect_pass": [f"*{name}*COMPLETE*", "*RC=0*"],
            "expect_fail": ["*ABEND*", "*ABNORMAL*"],
            "retry": 0,
            "delay": 0,
        })

    return steps


# ═══════════════════════════════════════════════════════════════
# RECOVERY SECTION
# ═══════════════════════════════════════════════════════════════

def _section_recovery(name: str, entry: ParsedEntry) -> str:
    """Build recovery processing section."""
    lines = [
        "* ── Recovery Processing ───────────────────────────────────────",
        f"* Recovery actions for {name} on test failure",
        "",
        f"* On RC=4 (Warning):",
        f'SEND "ZDSYS TRACE {name}"',
        f"WAIT 10",
        f'EXPECT "*TRACE*" PASS',
        f"RETRY 2",
        f"DELAY 5",
        "",
        f"* On RC=8 (Error):",
        f'SEND "ZDSYS DUMP {name}"',
        f"WAIT 15",
        f'EXPECT "*DUMP*COMPLETE*" PASS',
        f'EXPECT "*DUMP*FAIL*" FAIL',
        "",
        f"* On RC=12 (Severe):",
        f'SEND "ZDSYS SNAP {name}"',
        f"WAIT 30",
        f'EXPECT "*SNAP*COMPLETE*" PASS',
        f'EXPECT "*SNAP*FAIL*" FAIL',
        "",
    ]

    if entry.error_points:
        lines.append(f"* Entry-specific error paths:")
        for ep in entry.error_points[:5]:
            label = ep.split()[0] if ep.split() else "UNKNOWN"
            lines.append(f"*   Error point: {label[:40]}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# ORIGINAL STEP TABLE (backward compatibility)
# ═══════════════════════════════════════════════════════════════

def _original_step_table(entry: ParsedEntry) -> str:
    """Render the original-format step table for backward compatibility."""
    lines = [
        "* ── Step Summary Table ────────────────────────────────────────",
        "",
    ]

    header = (
        _pad("STEP", 7)
        + _pad("ACTION", 22)
        + _pad("ENTRY", 14)
        + _pad("CONDITION", 22)
        + "NEXT"
    )
    lines.append(header)
    lines.append("─" * 80)

    steps = _build_legacy_steps(entry)
    for s in steps:
        row = (
            _pad(s["step"], 7)
            + _pad(s["action"], 22)
            + _pad(s["entry"], 14)
            + _pad(s["condition"], 22)
            + s["next"]
        )
        lines.append(row)

    lines.append("─" * 80)
    lines.append(f"TOTAL STEPS: {len(steps)}")
    lines.append("")

    return "\n".join(lines)


def _build_legacy_steps(entry: ParsedEntry) -> list[dict]:
    """Build legacy TDRV step list (original format, preserved)."""
    steps = []
    step_num = 1
    name = entry.name
    macro_names = {m.name for m in entry.macros}
    has_enter = bool(macro_names & {"ENTER", "ENTRC", "ENPTS"})

    steps.append({
        "step": str(step_num).zfill(2),
        "action": "ENTRY INITIALIZATION" if has_enter else "RECEIVE REQUEST",
        "entry": name,
        "condition": "ENTER MACRO" if has_enter else "INPUT RECEIVED",
        "next": str(step_num + 1).zfill(2),
    })
    step_num += 1

    has_validation = any(i.category == "compare" for i in entry.instructions)
    if has_validation:
        steps.append({
            "step": str(step_num).zfill(2),
            "action": "VALIDATE INPUT",
            "entry": f"{name}_V",
            "condition": "VALID",
            "next": str(step_num + 1).zfill(2),
        })
        step_num += 1

    if entry.file_ops:
        steps.append({
            "step": str(step_num).zfill(2),
            "action": "FILE ACCESS",
            "entry": f"{name}_F",
            "condition": "RECORD FOUND",
            "next": str(step_num + 1).zfill(2),
        })
        step_num += 1

    if macro_names & {"PNRCC", "PNRAC"}:
        steps.append({
            "step": str(step_num).zfill(2),
            "action": "PNR PROCESSING",
            "entry": f"{name}_PNR",
            "condition": "PNR ACCESSED",
            "next": str(step_num + 1).zfill(2),
        })
        step_num += 1

    has_data = any(i.category in ("data", "arithmetic") for i in entry.instructions)
    if has_data:
        steps.append({
            "step": str(step_num).zfill(2),
            "action": "PROCESS DATA",
            "entry": f"{name}_P",
            "condition": "SUCCESS",
            "next": str(step_num + 1).zfill(2),
        })
        step_num += 1

    if macro_names & {"SERVC", "SVCRC"}:
        steps.append({
            "step": str(step_num).zfill(2),
            "action": "SERVICE CALL",
            "entry": f"{name}_S",
            "condition": "SERVICE OK",
            "next": str(step_num + 1).zfill(2),
        })
        step_num += 1

    if entry.error_points:
        steps.append({
            "step": str(step_num).zfill(2),
            "action": "ERROR HANDLING",
            "entry": f"{name}_E",
            "condition": "ERROR DETECTED",
            "next": str(step_num + 1).zfill(2),
        })
        step_num += 1

    if macro_names & {"RELCC", "RELFC", "RLASC"}:
        steps.append({
            "step": str(step_num).zfill(2),
            "action": "RELEASE STORAGE",
            "entry": f"{name}_REL",
            "condition": "RELEASED",
            "next": str(step_num + 1).zfill(2),
        })
        step_num += 1

    has_exit = bool(macro_names & {"EXITC", "EXITN", "BACKC", "BACK"})
    steps.append({
        "step": str(step_num).zfill(2),
        "action": "EXIT / RETURN" if has_exit else "RETURN RESPONSE",
        "entry": f"{name}_R",
        "condition": "COMPLETE",
        "next": "END",
    })

    return steps


def _count_recovery_steps(entry: ParsedEntry) -> int:
    """Count recovery-related steps."""
    count = 3  # Base RC=4, RC=8, RC=12
    if entry.error_points:
        count += min(len(entry.error_points), 5)
    return count
