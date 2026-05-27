"""
STS Coder — VAR File Generator (RAVEN Format)
================================================
Generates production-grade IBM z/TPF Operations Server VAR files.
Produces proper RAVEN automation format with:
  - VARIATION_DESCRIPTION
  - START_UP_TASKS
  - VARIATION_CMD
  - VARIATION  (message traps, automation triggers, recovery)
  - SHUTDOWN_TASKS

Supports console message monitoring, pattern matching, trigger
automation flows, recovery actions, REXX script launches,
event-driven automation, and startup/shutdown lifecycle.
"""

from datetime import datetime, timezone
from parser.tpf_parser import ParsedEntry


def _pad(text: str, width: int) -> str:
    """Left-justify text within a fixed-width column."""
    return str(text).ljust(width)


# ═══════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_var_file(entry: ParsedEntry) -> str:
    """Generate complete IBM z/TPF RAVEN VAR file from ParsedEntry."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    name = entry.name
    seg = entry.segment
    purpose = entry.purpose or "TPF transaction processing"
    macro_names = {m.name for m in entry.macros}
    lines: list[str] = []

    # ── File Header ──
    lines.append("*" * 72)
    lines.append(f"* VAR FILE — {name}")
    lines.append(f"* Segment:    {seg}")
    lines.append(f"* Purpose:    {purpose}")
    lines.append(f"* Generated:  STS Coder | {ts}")
    lines.append("*" * 72)
    lines.append("")

    # ── VARIATION_DESCRIPTION ──
    lines.append(_section_variation_description(name, seg, purpose, entry))

    # ── START_UP_TASKS ──
    lines.append(_section_startup_tasks(name, seg, macro_names, entry))

    # ── VARIATION_CMD ──
    lines.append(_section_variation_cmd(name, seg, entry))

    # ── VARIATION (main block) ──
    lines.append(_section_variation(name, seg, purpose, macro_names, entry))

    # ── SHUTDOWN_TASKS ──
    lines.append(_section_shutdown_tasks(name, seg, macro_names, entry))

    # ── Footer ──
    lines.append("*" * 72)
    lines.append(f"* END OF VAR — {name}")
    lines.append("*" * 72)

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# SECTION BUILDERS
# ═══════════════════════════════════════════════════════════════

def _section_variation_description(
    name: str, seg: str, purpose: str, entry: ParsedEntry
) -> str:
    """Build the VARIATION_DESCRIPTION section."""
    dep_list = ", ".join(entry.dependencies[:8]) if entry.dependencies else "NONE"
    file_list = ", ".join(entry.file_ops[:6]) if entry.file_ops else "NONE"
    macro_list = ", ".join(m.name for m in entry.macros[:8]) if entry.macros else "NONE"

    lines = [
        "* ──────────────────────────────────────────────────────────────",
        "* VARIATION DESCRIPTION",
        "* ──────────────────────────────────────────────────────────────",
        f"VARIATION_DESCRIPTION: {name} — {purpose}",
        f"*   Entry:          {name}",
        f"*   Segment:        {seg}",
        f"*   Purpose:        {purpose}",
        f"*   Dependencies:   {dep_list}",
        f"*   File Refs:      {file_list}",
        f"*   Macros:         {macro_list}",
        f"*   Variables:      {len(entry.variables)} defined",
        f"*   Error Points:   {len(entry.error_points)} detected",
        f"*   Line Count:     {entry.line_count}",
        "*",
        "*   This variation monitors entry execution, traps console",
        "*   messages, triggers automation flows on defined patterns,",
        "*   and manages recovery on error conditions.",
        "",
    ]
    return "\n".join(lines)


def _section_startup_tasks(
    name: str, seg: str, macro_names: set, entry: ParsedEntry
) -> str:
    """Build the START_UP_TASKS section."""
    lines = [
        "* ──────────────────────────────────────────────────────────────",
        "* START_UP TASKS",
        "* ──────────────────────────────────────────────────────────────",
        f"START_UP_TASKS:",
        f"  * Initialize RAVEN monitoring for {name}",
        f"  LOG 'RAVEN: Initializing VAR for {name} segment {seg}'",
    ]

    # Entry-point initialization
    if macro_names & {"ENTER", "ENTRC", "ENPTS"}:
        lines.append(f"  ZOSRV STATUS")
        lines.append(f"  * Verify Operations Server is active")

    # File system readiness check
    if entry.file_ops:
        file_refs = ", ".join(entry.file_ops[:4])
        lines.append(f"  * Verify file accessibility: {file_refs}")
        lines.append(f"  ZDFIL STATUS")

    # ECB verification
    if entry.ecb_refs:
        lines.append(f"  * Verify ECB availability: {', '.join(entry.ecb_refs[:4])}")
        lines.append(f"  ZDECB STATUS")

    # Storage check
    if macro_names & {"GETCC", "GETFC", "GLOBZ", "GLOBS", "ALASC"}:
        lines.append(f"  * Verify storage pools")
        lines.append(f"  ZDSYS POOL STATUS")

    # Timer initialization
    if macro_names & {"TIMEC"}:
        lines.append(f"  * Timer service initialization")
        lines.append(f"  ZDTIM STATUS")

    lines.append(f"  EXEC REXX '{name}_STARTUP.rexx'")
    lines.append(f"  LOG 'RAVEN: Startup complete for {name}'")
    lines.append("")
    return "\n".join(lines)


def _section_variation_cmd(name: str, seg: str, entry: ParsedEntry) -> str:
    """Build the VARIATION_CMD monitoring commands section."""
    macro_names = {m.name for m in entry.macros}
    lines = [
        "* ──────────────────────────────────────────────────────────────",
        "* VARIATION_CMD — Monitoring Commands",
        "* ──────────────────────────────────────────────────────────────",
        f"VARIATION_CMD:",
        f"  * Periodic health monitoring for {name}",
        f"  ZDSYS STATUS",
        f"  ZDPRF {name}",
    ]

    if entry.file_ops:
        lines.append(f"  ZDFIL {', '.join(entry.file_ops[:3])}")

    if entry.ecb_refs:
        lines.append(f"  ZDECB {', '.join(entry.ecb_refs[:3])}")

    if macro_names & {"SERVC", "SVCRC"}:
        lines.append(f"  ZOSRV STATUS")

    if macro_names & {"PNRCC", "PNRAC"}:
        lines.append(f"  ZDPNR STATUS")

    if macro_names & {"GETCC", "GETFC", "GLOBZ", "GLOBS"}:
        lines.append(f"  ZDSYS POOL STATUS")

    lines.append(f"  LOG 'RAVEN: Monitoring cycle for {name} complete'")
    lines.append("")
    return "\n".join(lines)


def _section_variation(
    name: str, seg: str, purpose: str, macro_names: set, entry: ParsedEntry
) -> str:
    """Build the main VARIATION block with message traps and automation."""
    lines = [
        "* ──────────────────────────────────────────────────────────────",
        "* VARIATION — Main Automation Block",
        "* ──────────────────────────────────────────────────────────────",
        f"VARIATION: {name}_{seg}",
        f"*   Automation for: {purpose}",
        "",
    ]

    # ── Message Traps: Console Message Monitoring ──
    lines.append("  * ── Console Message Monitoring ──────────────────────────")
    lines.append(f"  TRAP MSG '{name}*COMPLETE*'")
    lines.append(f"    ACTION LOG 'RAVEN: {name} completed successfully'")
    lines.append(f"    ACTION EXEC REXX '{name}_ONCOMPLETE.rexx'")
    lines.append("")

    lines.append(f"  TRAP MSG '{name}*STARTED*'")
    lines.append(f"    ACTION LOG 'RAVEN: {name} execution started'")
    lines.append("")

    # ── Error Pattern Traps ──
    lines.append("  * ── Error Pattern Monitoring ─────────────────────────────")
    if entry.error_points:
        for idx, ep in enumerate(entry.error_points[:6]):
            # Extract a keyword from the error point for pattern matching
            err_kw = _extract_error_keyword(ep)
            lines.append(f"  TRAP MSG '*{err_kw}*'")
            lines.append(f"    ACTION LOG 'ALERT: {name} error — {err_kw}'")
            lines.append(f"    ACTION EXEC REXX '{name}_RECOVERY.rexx' '{err_kw}'")
            lines.append(f"    ACTION NOTIFY OPERATOR '{name}: Error detected — {err_kw}'")
            lines.append("")
    else:
        lines.append(f"  TRAP MSG '{name}*ERROR*'")
        lines.append(f"    ACTION LOG 'ALERT: {name} error detected'")
        lines.append(f"    ACTION EXEC REXX '{name}_RECOVERY.rexx'")
        lines.append(f"    ACTION NOTIFY OPERATOR '{name}: Error — investigate immediately'")
        lines.append("")

    lines.append(f"  TRAP MSG '{name}*ABEND*'")
    lines.append(f"    ACTION LOG 'CRITICAL: {name} ABEND detected'")
    lines.append(f"    ACTION EXEC REXX '{name}_ABEND_RECOVERY.rexx'")
    lines.append(f"    ACTION NOTIFY OPERATOR '{name}: ABEND — immediate attention required'")
    lines.append("")

    # ── Automation Triggers ──
    lines.append("  * ── Automation Triggers ─────────────────────────────────")

    if macro_names & {"FILEC", "FINDA", "FINDC", "FINDS"}:
        lines.append(f"  TRIGGER ON FILE_ACCESS")
        lines.append(f"    ACTION LOG 'RAVEN: {name} file access detected'")
        lines.append(f"    ACTION MONITOR FILE_IO {name}")
        lines.append("")

    if macro_names & {"SERVC", "SVCRC"}:
        lines.append(f"  TRIGGER ON SERVICE_CALL")
        lines.append(f"    ACTION LOG 'RAVEN: {name} service call initiated'")
        lines.append(f"    ACTION MONITOR SERVICE {name}")
        lines.append("")

    if macro_names & {"PNRCC", "PNRAC"}:
        lines.append(f"  TRIGGER ON PNR_ACCESS")
        lines.append(f"    ACTION LOG 'RAVEN: {name} PNR access'")
        lines.append(f"    ACTION MONITOR PNR {name}")
        lines.append("")

    if macro_names & {"TIMEC"}:
        lines.append(f"  TRIGGER ON TIMER_EVENT")
        lines.append(f"    ACTION LOG 'RAVEN: {name} timer event fired'")
        lines.append(f"    ACTION EXEC REXX '{name}_TIMER.rexx'")
        lines.append("")

    if macro_names & {"SENDC", "SENDM"}:
        lines.append(f"  TRIGGER ON MESSAGE_SEND")
        lines.append(f"    ACTION LOG 'RAVEN: {name} outbound message'")
        lines.append("")

    # ── Event-Driven Automation ──
    lines.append("  * ── Event-Driven Automation ──────────────────────────────")
    lines.append(f"  EVENT SCHEDULE INTERVAL=300")
    lines.append(f"    ACTION EXEC REXX '{name}_HEALTH_CHECK.rexx'")
    lines.append(f"    ACTION LOG 'RAVEN: Periodic health check for {name}'")
    lines.append("")

    lines.append(f"  EVENT ON THRESHOLD CPU>80")
    lines.append(f"    ACTION LOG 'WARNING: {name} high CPU utilization'")
    lines.append(f"    ACTION NOTIFY OPERATOR '{name}: CPU threshold exceeded'")
    lines.append("")

    # ── Recovery Actions ──
    lines.append("  * ── Recovery Actions ──────────────────────────────────────")
    lines.append(f"  RECOVERY ON RC=4")
    lines.append(f"    ACTION LOG 'RAVEN: {name} RC=4 — minor condition, retrying'")
    lines.append(f"    ACTION RETRY COUNT=3 DELAY=5")
    lines.append("")
    lines.append(f"  RECOVERY ON RC=8")
    lines.append(f"    ACTION LOG 'RAVEN: {name} RC=8 — error, escalating'")
    lines.append(f"    ACTION EXEC REXX '{name}_ESCALATE.rexx'")
    lines.append(f"    ACTION NOTIFY OPERATOR '{name}: RC=8 — requires investigation'")
    lines.append("")
    lines.append(f"  RECOVERY ON RC=12")
    lines.append(f"    ACTION LOG 'CRITICAL: {name} RC=12 — severe error'")
    lines.append(f"    ACTION EXEC REXX '{name}_CRITICAL_RECOVERY.rexx'")
    lines.append(f"    ACTION NOTIFY OPERATOR '{name}: RC=12 — immediate action required'")
    lines.append("")

    # ── REXX Script Launches ──
    lines.append("  * ── REXX Script Integration ──────────────────────────────")
    lines.append(f"  EXEC REXX '{name}_MONITOR.rexx' PARM='{seg}'")
    lines.append(f"  EXEC REXX '{name}_VALIDATE.rexx'")
    lines.append("")

    # ── Operational Logging ──
    lines.append("  * ── Operational Logging ────────────────────────────────")
    lines.append(f"  LOG LEVEL=INFO  'RAVEN: {name} variation active'")
    lines.append(f"  LOG LEVEL=DEBUG 'RAVEN: Monitoring {len(entry.variables)} variables'")
    lines.append(f"  LOG LEVEL=DEBUG 'RAVEN: {len(entry.macros)} macros tracked'")
    lines.append(f"  LOG LEVEL=DEBUG 'RAVEN: {len(entry.error_points)} error points monitored'")
    lines.append("")

    # ── Static Variable Table (preserved from original) ──
    lines.append(_variable_table(entry))

    return "\n".join(lines)


def _section_shutdown_tasks(
    name: str, seg: str, macro_names: set, entry: ParsedEntry
) -> str:
    """Build the SHUTDOWN_TASKS section."""
    lines = [
        "* ──────────────────────────────────────────────────────────────",
        "* SHUTDOWN_TASKS",
        "* ──────────────────────────────────────────────────────────────",
        f"SHUTDOWN_TASKS:",
        f"  * Graceful shutdown for {name}",
        f"  LOG 'RAVEN: Initiating shutdown for {name}'",
    ]

    # Release storage
    if macro_names & {"GETCC", "RELCC", "GETFC", "RELFC", "ALASC", "RLASC"}:
        lines.append(f"  * Release allocated storage")
        lines.append(f"  ZDSYS POOL RELEASE")

    # File cleanup
    if entry.file_ops:
        lines.append(f"  * Close open file references")
        lines.append(f"  ZDFIL CLOSE ALL")

    # ECB cleanup
    if entry.ecb_refs:
        lines.append(f"  * Release ECB resources")
        lines.append(f"  ZDECB RELEASE ALL")

    # Timer cleanup
    if macro_names & {"TIMEC"}:
        lines.append(f"  * Cancel active timers")
        lines.append(f"  ZDTIM CANCEL ALL")

    lines.append(f"  EXEC REXX '{name}_SHUTDOWN.rexx'")
    lines.append(f"  LOG 'RAVEN: Shutdown complete for {name}'")
    lines.append(f"  * Deactivate all message traps")
    lines.append(f"  TRAP DEACTIVATE ALL")
    lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _variable_table(entry: ParsedEntry) -> str:
    """Render the static variable table as a sub-section."""
    lines = [
        "  * ── Variable Definition Table ──────────────────────────────",
        "",
    ]

    header = (
        "  " + _pad("VAR_NAME", 18)
        + _pad("TYPE", 8)
        + _pad("LEN", 6)
        + _pad("SOURCE", 14)
        + _pad("DEFAULT", 12)
        + _pad("VALIDATION", 18)
        + "DESCRIPTION"
    )
    lines.append(header)
    lines.append("  " + "─" * 100)

    vars_to_render = entry.variables if entry.variables else _default_vars()

    for v in vars_to_render:
        row = (
            "  " + _pad(v.name, 18)
            + _pad(v.var_type, 8)
            + _pad(v.length, 6)
            + _pad(v.source, 14)
            + _pad(v.default, 12)
            + _pad(v.validation, 18)
            + v.description
        )
        lines.append(row)

    lines.append("  " + "─" * 100)
    lines.append(f"  TOTAL VARIABLES: {len(vars_to_render)}")
    lines.append("")

    return "\n".join(lines)


def _extract_error_keyword(error_line: str) -> str:
    """Extract a meaningful keyword from an error point line."""
    import re
    # Try to find a label-like identifier
    m = re.match(r"^\s*(\w+)", error_line)
    if m:
        word = m.group(1).upper()
        if len(word) >= 3:
            return word
    return "ERROR"


def _default_vars():
    """Fallback variables when none are extracted."""
    from parser.tpf_parser import Variable

    return [
        Variable(
            name="ENTRY_ID", directive="DS", operand="CL8",
            var_type="CHAR", length="08", source="SYSTEM",
            default="SPACES", validation="NOT NULL", description="Entry Identifier",
        ),
        Variable(
            name="ERR_CODE", directive="DS", operand="CL4",
            var_type="CHAR", length="04", source="SYSTEM",
            default="0000", validation="NUMERIC", description="Error Code",
        ),
        Variable(
            name="RET_CODE", directive="DS", operand="F",
            var_type="BIN", length="04", source="SYSTEM",
            default="0", validation="NUMERIC", description="Return Code",
        ),
    ]
