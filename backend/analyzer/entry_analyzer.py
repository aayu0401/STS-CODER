"""
STS Coder — Entry Analyzer & Recommendation Engine
=====================================================
Provides structured analysis output and engineering
recommendations for TPF entries.
"""

from parser.tpf_parser import ParsedEntry


def generate_analysis(entry: ParsedEntry) -> dict:
    """Generate structured analysis dict from ParsedEntry."""
    macro_names = [m.name for m in entry.macros]

    return {
        "entry_name": entry.name,
        "segment": entry.segment,
        "purpose": entry.purpose,
        "line_count": entry.line_count,
        "statistics": {
            "variables": len(entry.variables),
            "macros": len(entry.macros),
            "branches": len(entry.branches),
            "instructions": len(entry.instructions),
            "file_operations": len(entry.file_ops),
            "error_points": len(entry.error_points),
            "ecb_references": len(entry.ecb_refs),
            "labels": len(entry.labels),
        },
        "inputs": entry.inputs,
        "outputs": entry.outputs,
        "macros_called": macro_names,
        "file_references": entry.file_ops,
        "ecb_references": entry.ecb_refs,
        "labels": entry.labels,
        "error_handling": entry.error_points[:10],
        "instruction_breakdown": _instruction_breakdown(entry),
        "branch_targets": [b.target for b in entry.branches[:20]],
        "dependencies": entry.dependencies,
        "complexity_score": _compute_complexity(entry),
    }


def generate_recommendations(entry: ParsedEntry) -> list[dict]:
    """Generate engineering recommendations list."""
    recs: list[dict] = []
    macro_names = {m.name for m in entry.macros}

    # Error handling
    if not entry.error_points:
        recs.append({
            "severity": "WARNING",
            "category": "ERROR_HANDLING",
            "text": "No explicit error handling detected. Add structured error paths with ERR labels.",
        })

    # Exit macros
    if not macro_names & {"EXITC", "EXITN", "BACKC", "BACK"}:
        recs.append({
            "severity": "WARNING",
            "category": "EXIT_LOGIC",
            "text": "No EXIT/BACK macro detected. Ensure proper entry exit is defined to prevent ECB leaks.",
        })

    # File access without validation
    if entry.file_ops and not any(i.category == "compare" for i in entry.instructions):
        recs.append({
            "severity": "WARNING",
            "category": "VALIDATION",
            "text": "File access without input validation detected. Add CLI/CLC checks before FILEC/FINDA calls.",
        })

    # Variable count
    if len(entry.variables) < 3:
        recs.append({
            "severity": "WARNING",
            "category": "COMPLETENESS",
            "text": "Very few variables extracted. Entry may require manual review or includes external DSECTs.",
        })

    # Branch complexity
    if len(entry.branches) > 15:
        recs.append({
            "severity": "INFO",
            "category": "COMPLEXITY",
            "text": f"High branch complexity ({len(entry.branches)} branches). Consider modularizing into sub-entries.",
        })

    # ECB safety
    if entry.ecb_refs:
        recs.append({
            "severity": "INFO",
            "category": "ECB_SAFETY",
            "text": f"ECB references detected ({len(entry.ecb_refs)}). Verify ECB-safe logic across all paths.",
        })

    # Storage management
    has_get = macro_names & {"GETCC", "GETFC", "ALASC", "CRUSA"}
    has_rel = macro_names & {"RELCC", "RELFC", "RLASC"}
    if has_get and not has_rel:
        recs.append({
            "severity": "WARNING",
            "category": "STORAGE",
            "text": "Storage acquisition without release detected. Ensure RELCC/RELFC on all exit paths.",
        })

    # PNR without protection
    if macro_names & {"PNRCC", "PNRAC"}:
        recs.append({
            "severity": "INFO",
            "category": "PNR",
            "text": "PNR access detected. Verify simultaneous access protection and lock handling.",
        })

    # General
    recs.append({
        "severity": "INFO",
        "category": "VALIDATION",
        "text": "Validate all extracted variables against live TPF system before production use.",
    })
    recs.append({
        "severity": "INFO",
        "category": "DOCUMENTATION",
        "text": "Review ECB usage, storage allocation, and transaction safety for production readiness.",
    })

    return recs


def _instruction_breakdown(entry: ParsedEntry) -> dict:
    """Count instructions by category."""
    counts: dict[str, int] = {}
    for inst in entry.instructions:
        counts[inst.category] = counts.get(inst.category, 0) + 1
    return counts


def _compute_complexity(entry: ParsedEntry) -> dict:
    """Compute a simple complexity score."""
    branch_score = min(len(entry.branches) * 2, 40)
    var_score = min(len(entry.variables), 20)
    macro_score = min(len(entry.macros) * 3, 20)
    error_score = 10 if entry.error_points else 0
    file_score = min(len(entry.file_ops) * 5, 10)
    total = branch_score + var_score + macro_score + error_score + file_score

    if total < 20:
        level = "LOW"
    elif total < 50:
        level = "MODERATE"
    elif total < 80:
        level = "HIGH"
    else:
        level = "VERY HIGH"

    return {"score": total, "level": level, "max": 100}
