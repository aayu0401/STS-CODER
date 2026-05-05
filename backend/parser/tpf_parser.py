"""
STS Coder — IBM z/TPF Entry Parser
===================================
Production-grade parser for IBM z/TPF assembly entries.
Extracts: variables, macros, labels, branches, file ops,
error handling, instructions, and structural metadata.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ═══════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════

@dataclass
class Variable:
    name: str
    directive: str          # DS, DC, EQU
    operand: str
    var_type: str = ""      # CHAR, BIN, PACK, HEX, ADDR, EQU
    length: str = "UNK"
    source: str = "INTERNAL"
    default: str = "SPACES"
    validation: str = "NONE"
    description: str = ""
    line_number: int = 0


@dataclass
class Branch:
    instruction: str        # B, BE, BNE, BH, BL, etc.
    target: str
    line_number: int = 0


@dataclass
class Instruction:
    category: str           # compare, data, arithmetic, control
    mnemonic: str
    operand: str
    line_number: int = 0


@dataclass
class MacroCall:
    name: str
    operands: str = ""
    line_number: int = 0


@dataclass
class ParsedEntry:
    name: str = "UNKNOWN"
    segment: str = "UNKNOWN"
    purpose: str = ""
    raw: str = ""
    line_count: int = 0

    variables: List[Variable] = field(default_factory=list)
    macros: List[MacroCall] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    branches: List[Branch] = field(default_factory=list)
    instructions: List[Instruction] = field(default_factory=list)
    file_ops: List[str] = field(default_factory=list)
    error_points: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    ecb_refs: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════
# PATTERN DEFINITIONS
# ═══════════════════════════════════════════

# TPF system macros (comprehensive list)
TPF_MACROS = {
    # Entry/Exit
    "ENTER", "ENTRC", "ENPTS", "EXITC", "EXITN", "BACKC", "BACK",
    # File access
    "FILEC", "FILEM", "FILEA", "FILED", "FILEL", "FILNC",
    "FINDA", "FINDC", "FINDS", "FINDR",
    # Record management
    "CRUSA", "CRUSC", "CRUSD", "GETCC", "RELCC", "LODRF",
    # Storage
    "GLOBZ", "GLOBS", "GETFC", "RELFC", "ALASC", "RLASC",
    # Service
    "SERVC", "SVCRC",
    # Communication
    "SENDC", "SENDM",
    # PNR
    "PNRCC", "PNRAC",
    # Miscellaneous
    "CNTRC", "CINFC", "DETAC", "ATTAC", "SWAPC", "CREMC",
    "TIMEC", "SYSRA", "LOADC", "DETRC", "ATTRC",
}

# Branch mnemonics
BRANCH_MNEMONICS = {
    "B", "BE", "BNE", "BH", "BL", "BNH", "BNL",
    "BC", "BCR", "BCT", "BCTR", "BAL", "BALR", "BAS", "BASR",
    "BXH", "BXLE", "BRC", "BRAS", "BRASL", "BRE", "BRNE",
    "BRH", "BRL", "BRNH", "BRNL",
}

# Compare/Test instructions
COMPARE_MNEMONICS = {
    "CLI", "CLC", "C", "CH", "CR", "CE", "CP",
    "TM", "TRT", "CLCL", "CLM", "CLR",
}

# Load/Store/Move instructions
DATA_MNEMONICS = {
    "L", "LA", "LH", "LR", "LM", "LTR", "LNR", "LPR", "LCR",
    "ST", "STH", "STM", "STC", "STCM",
    "MVC", "MVI", "MVCL", "MVZ", "MVN", "MVO",
    "IC", "ICM",
    "XC", "OC", "NC", "XR", "OR", "NR",
}

# Arithmetic instructions
ARITH_MNEMONICS = {
    "A", "AH", "AR", "AL", "ALR",
    "S", "SH", "SR", "SL", "SLR",
    "M", "MH", "MR",
    "D", "DR",
    "AP", "SP", "MP", "DP", "ZAP",
    "SRP", "CVB", "CVD",
    "SLA", "SRA", "SLDA", "SRDA", "SLL", "SRL", "SLDL", "SRDL",
}


# ═══════════════════════════════════════════
# COMPILED REGEX PATTERNS
# ═══════════════════════════════════════════

RE_CSECT = re.compile(r"^(\w+)\s+CSECT", re.IGNORECASE)
RE_LABEL_DS0H = re.compile(r"^(\w+)\s+DS\s+0H", re.IGNORECASE)
RE_LABEL_EQU_STAR = re.compile(r"^(\w+)\s+EQU\s+\*", re.IGNORECASE)
RE_VARIABLE = re.compile(r"^(\w+)\s+(DS|DC)\s+(.+?)(?:\s+.*)?$", re.IGNORECASE)
RE_EQUATE = re.compile(r"^(\w+)\s+EQU\s+(.+?)(?:\s+.*)?$", re.IGNORECASE)
RE_COMMENT = re.compile(r"^\*")
RE_CONTINUATION = re.compile(r"^\s{15,}")
RE_FILE_REF = re.compile(r"\b(FILE[A-Z]*|FIND[A-Z]*)\b", re.IGNORECASE)
RE_ECB_REF = re.compile(r"\bECB\w*\b", re.IGNORECASE)
RE_ERROR_KW = re.compile(
    r"\b(ERR|ERROR|FAIL|INVALID|ABORT|REJECT|NOTFND|NFOUND|BADDATA|ERRXIT)\b",
    re.IGNORECASE,
)
RE_INPUT_VAR = re.compile(r"(INPUT|REQ|RECV|IN_|INP_|I_)", re.IGNORECASE)
RE_OUTPUT_VAR = re.compile(r"(OUTPUT|RESP|OUT_|RESULT|O_|RSP_)", re.IGNORECASE)
RE_LENGTH_CL = re.compile(r"CL(\d+)", re.IGNORECASE)


# ═══════════════════════════════════════════
# PARSER CLASS
# ═══════════════════════════════════════════

class TPFParser:
    """
    Parses raw IBM z/TPF assembly source into a structured ParsedEntry.
    Deterministic — no probabilistic inference.
    """

    def __init__(self):
        self._build_mnemonic_lookup()

    def _build_mnemonic_lookup(self):
        """Pre-compile mnemonic sets for fast lookup."""
        self._branch_set = {m.upper() for m in BRANCH_MNEMONICS}
        self._compare_set = {m.upper() for m in COMPARE_MNEMONICS}
        self._data_set = {m.upper() for m in DATA_MNEMONICS}
        self._arith_set = {m.upper() for m in ARITH_MNEMONICS}
        self._macro_set = {m.upper() for m in TPF_MACROS}

    def parse(self, raw_text: str, entry_name: str = "", segment: str = "") -> ParsedEntry:
        """
        Main parse entry point.
        Accepts raw TPF assembly text and returns ParsedEntry.
        """
        result = ParsedEntry(raw=raw_text)
        lines = raw_text.split("\n")
        result.line_count = len(lines)

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip()

            # Skip empty or comment-only lines
            if not line.strip() or RE_COMMENT.match(line):
                continue

            self._parse_line(line, line_num, result)

        # Override with user-supplied metadata
        if entry_name:
            result.name = entry_name.upper()
        if segment:
            result.segment = segment.upper()

        # Post-processing
        self._deduplicate(result)
        self._infer_purpose(result)
        self._classify_io_vars(result)
        self._extract_dependencies(result)

        return result

    def _parse_line(self, line: str, line_num: int, result: ParsedEntry):
        """Parse a single source line."""

        # ── CSECT detection ──
        m = RE_CSECT.match(line)
        if m:
            if result.name == "UNKNOWN":
                result.name = m.group(1).upper()
            result.labels.append(m.group(1).upper())
            return

        # ── Label DS 0H ──
        m = RE_LABEL_DS0H.match(line)
        if m:
            result.labels.append(m.group(1).upper())
            return

        # ── Label EQU * ──
        m = RE_LABEL_EQU_STAR.match(line)
        if m:
            result.labels.append(m.group(1).upper())
            return

        # ── Variable (DS/DC) ──
        m = RE_VARIABLE.match(line)
        if m:
            var = self._parse_variable(m.group(1), m.group(2), m.group(3), line_num)
            result.variables.append(var)
            return

        # ── Equate ──
        m = RE_EQUATE.match(line)
        if m and not RE_LABEL_EQU_STAR.match(line):
            var = Variable(
                name=m.group(1).upper(),
                directive="EQU",
                operand=m.group(2).strip(),
                var_type="EQU",
                length="N/A",
                source="CONSTANT",
                default=m.group(2).strip(),
                validation="CONSTANT",
                description=f"Equate: {m.group(1).upper()}",
                line_number=line_num,
            )
            result.variables.append(var)
            return

        # ── Instruction parsing ──
        # Strip label from front if present
        parts = line.split()
        if not parts:
            return

        # Determine if first token is a label or mnemonic
        idx = 0
        potential_label = parts[0]
        mnemonic_upper = potential_label.upper()

        # If first token is not a known mnemonic, it may be a label
        if (
            mnemonic_upper not in self._branch_set
            and mnemonic_upper not in self._compare_set
            and mnemonic_upper not in self._data_set
            and mnemonic_upper not in self._arith_set
            and mnemonic_upper not in self._macro_set
        ):
            # Might be a labelled instruction line
            idx = 1
            if len(parts) > 1:
                mnemonic_upper = parts[1].upper()
            else:
                return

        mnemonic = mnemonic_upper
        operand = " ".join(parts[idx + 1:]) if len(parts) > idx + 1 else ""
        # Strip inline comments (after a space-separated sequence)
        operand = operand.split("  ")[0].strip()

        # ── TPF Macro ──
        if mnemonic in self._macro_set:
            result.macros.append(MacroCall(name=mnemonic, operands=operand, line_number=line_num))

        # ── Branch ──
        elif mnemonic in self._branch_set:
            target = operand.split(",")[0].strip() if operand else "UNKNOWN"
            result.branches.append(Branch(instruction=mnemonic, target=target, line_number=line_num))

        # ── Compare ──
        elif mnemonic in self._compare_set:
            result.instructions.append(
                Instruction(category="compare", mnemonic=mnemonic, operand=operand, line_number=line_num)
            )

        # ── Data movement ──
        elif mnemonic in self._data_set:
            result.instructions.append(
                Instruction(category="data", mnemonic=mnemonic, operand=operand, line_number=line_num)
            )

        # ── Arithmetic ──
        elif mnemonic in self._arith_set:
            result.instructions.append(
                Instruction(category="arithmetic", mnemonic=mnemonic, operand=operand, line_number=line_num)
            )

        # ── File references ──
        if RE_FILE_REF.search(line):
            for fm in RE_FILE_REF.finditer(line):
                result.file_ops.append(fm.group(0).upper())

        # ── ECB references ──
        if RE_ECB_REF.search(line):
            for em in RE_ECB_REF.finditer(line):
                result.ecb_refs.append(em.group(0).upper())

        # ── Error keywords ──
        if RE_ERROR_KW.search(line):
            result.error_points.append(line.strip())

    def _parse_variable(self, name: str, directive: str, operand: str, line_num: int) -> Variable:
        """Create Variable from DS/DC definition."""
        name_upper = name.upper()
        dir_upper = directive.upper()
        operand_clean = operand.strip()

        var_type = self._infer_type(dir_upper, operand_clean)
        length = self._infer_length(operand_clean)
        source = self._infer_source(name_upper)
        default = self._infer_default(dir_upper, var_type, operand_clean)
        validation = self._infer_validation(var_type, name_upper)

        return Variable(
            name=name_upper,
            directive=dir_upper,
            operand=operand_clean,
            var_type=var_type,
            length=length,
            source=source,
            default=default,
            validation=validation,
            description=name_upper,
            line_number=line_num,
        )

    # ── Type inference ──
    @staticmethod
    def _infer_type(directive: str, operand: str) -> str:
        op = operand.upper().strip()
        if "CL" in op:
            return "CHAR"
        if op.startswith("F") or op == "F":
            return "BIN"
        if op.startswith("H") or op == "H":
            return "BIN"
        if op.startswith("D") or op == "D":
            return "BIN"
        if op.startswith("P"):
            return "PACK"
        if op.startswith("X"):
            return "HEX"
        if op.startswith("A") or op.startswith("V"):
            return "ADDR"
        if op.startswith("C"):
            return "CHAR"
        return "CHAR"

    # ── Length inference ──
    @staticmethod
    def _infer_length(operand: str) -> str:
        m = RE_LENGTH_CL.search(operand)
        if m:
            return m.group(1).zfill(2)
        op = operand.upper().strip()
        # Handle repeat counts like 3CL4 → length = 12
        rm = re.match(r"(\d+)CL(\d+)", op)
        if rm:
            return str(int(rm.group(1)) * int(rm.group(2))).zfill(2)
        if op.startswith("F") or op == "F":
            return "04"
        if op.startswith("H") or op == "H":
            return "02"
        if op.startswith("D") or op == "D":
            return "08"
        if op.startswith("X"):
            xm = re.match(r"X[L']?(\d+)?", op)
            return xm.group(1).zfill(2) if xm and xm.group(1) else "01"
        if op.startswith("P"):
            pm = re.match(r"PL?(\d+)", op)
            return pm.group(1).zfill(2) if pm and pm.group(1) else "UNK"
        if op.startswith("A"):
            return "04"
        return "UNK"

    # ── Source inference ──
    @staticmethod
    def _infer_source(name: str) -> str:
        if RE_INPUT_VAR.search(name):
            return "INPUT"
        if RE_OUTPUT_VAR.search(name):
            return "OUTPUT"
        if re.search(r"(FILE|REC|LOC|PNR|RECL)", name, re.IGNORECASE):
            return "FILE"
        if re.search(r"(ERR|RET|SYS|STAT|RC_|RETC)", name, re.IGNORECASE):
            return "SYSTEM"
        if re.search(r"(WK_|WORK|TEMP|TMP|W_)", name, re.IGNORECASE):
            return "WORK"
        return "INTERNAL"

    # ── Default inference ──
    @staticmethod
    def _infer_default(directive: str, var_type: str, operand: str) -> str:
        if directive == "DC":
            # Try to extract literal
            m = re.search(r"[CFHXPA]'([^']*)'", operand)
            if m:
                return m.group(1) if m.group(1) else "EMPTY"
        if var_type in ("CHAR",):
            return "SPACES"
        if var_type in ("BIN", "PACK"):
            return "0"
        if var_type == "HEX":
            return "X'00'"
        if var_type == "ADDR":
            return "0"
        return "SPACES"

    # ── Validation inference ──
    @staticmethod
    def _infer_validation(var_type: str, name: str) -> str:
        if re.search(r"(ID$|_ID|CODE|_CD|KEY)", name, re.IGNORECASE):
            return "NOT NULL"
        if var_type in ("BIN", "PACK"):
            return "NUMERIC"
        if re.search(r"(LOC|ADDR|PTR)", name, re.IGNORECASE):
            return "VALID ADDRESS"
        if re.search(r"(DATE|DT_)", name, re.IGNORECASE):
            return "DATE FORMAT"
        if re.search(r"(FLAG|FLG|IND)", name, re.IGNORECASE):
            return "BIT FIELD"
        return "NONE"

    # ── Post-processing ──
    @staticmethod
    def _deduplicate(result: ParsedEntry):
        seen_macros = set()
        unique_macros = []
        for mc in result.macros:
            if mc.name not in seen_macros:
                seen_macros.add(mc.name)
                unique_macros.append(mc)
        result.macros = unique_macros

        result.file_ops = list(dict.fromkeys(result.file_ops))
        result.labels = list(dict.fromkeys(result.labels))
        result.ecb_refs = list(dict.fromkeys(result.ecb_refs))

    @staticmethod
    def _infer_purpose(result: ParsedEntry):
        macro_names = {m.name for m in result.macros}
        if macro_names & {"FILEC", "FINDA", "FINDC", "FINDS"}:
            result.purpose = "File access and record retrieval"
        elif macro_names & {"CRUSA", "CRUSC", "CRUSD"}:
            result.purpose = "Record creation / update processing"
        elif macro_names & {"SERVC", "SVCRC"}:
            result.purpose = "Service call processing"
        elif macro_names & {"PNRCC", "PNRAC"}:
            result.purpose = "PNR processing"
        elif macro_names & {"SENDC", "SENDM"}:
            result.purpose = "Message / communication processing"
        elif macro_names & {"TIMEC"}:
            result.purpose = "Timer-based processing"
        else:
            result.purpose = "TPF transaction processing"

    @staticmethod
    def _classify_io_vars(result: ParsedEntry):
        for v in result.variables:
            if RE_INPUT_VAR.search(v.name):
                result.inputs.append(v.name)
            if RE_OUTPUT_VAR.search(v.name):
                result.outputs.append(v.name)
        if not result.inputs:
            result.inputs.append("UNKNOWN - Requires TPF validation")
        if not result.outputs:
            result.outputs.append("UNKNOWN - Requires TPF validation")

    @staticmethod
    def _extract_dependencies(result: ParsedEntry):
        for mc in result.macros:
            result.dependencies.append(mc.name)
        for fo in result.file_ops:
            if fo not in result.dependencies:
                result.dependencies.append(fo)
        if not result.dependencies:
            result.dependencies.append("UNKNOWN - Requires TPF validation")


# ═══════════════════════════════════════════
# MODULE-LEVEL CONVENIENCE
# ═══════════════════════════════════════════

_parser_instance = TPFParser()


def parse_tpf_entry(raw_text: str, entry_name: str = "", segment: str = "") -> ParsedEntry:
    """Module-level parse function."""
    return _parser_instance.parse(raw_text, entry_name, segment)
