"""
STS Coder — Comprehensive z/TPF Knowledge Base
Covers: Z-Commands, REXX/RAVEN, VAR, TDR, TDRV, ECB, Macros, System Responses
"""

# ─── Z-COMMAND DETAILED RESPONSES ───
ZCMD_RESPONSES = {
    "ZDSYS": {
        "purpose": "Display System Status",
        "syntax": "ZDSYS [ALL|CPU|MDB|XPC]",
        "description": "Displays comprehensive z/TPF system status including CPU utilization, MDB (Message Data Block) state, cross-processor communication metrics, and active subsystem states.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE/STANDBY",
            "CPU UTIL: xx.x%",
            "MDB STATE: NORMAL/DEGRADED",
            "ECB COUNT: nnnn ACTIVE",
            "POOL STATUS: nnnK FREE / nnnK USED",
            "XPC STATUS: CONNECTED/DISCONNECTED",
        ],
        "example": "ZDSYS ALL",
        "category": "System Status",
    },
    "ZDECB": {
        "purpose": "Display ECB Data Levels",
        "syntax": "ZDECB ecb_addr [D0|D1|...|DF] [HEX|CHAR]",
        "description": "Dumps ECB data levels (D0 through DF), registers, and specific core block contents for debugging. Essential for post-mortem analysis.",
        "output_fields": [
            "ECB ADDRESS: xxxxxxxx",
            "DATA LEVEL D0: xxxxxxxx xxxxxxxx ...",
            "GR0-GR15: register dump",
            "CE1CR0: input data area",
            "PROGRAM STATUS WORD (PSW)",
        ],
        "example": "ZDECB 0A3F00 D0 HEX",
        "category": "Diagnostic",
    },
    "ZSTAT": {
        "purpose": "System Statistics",
        "syntax": "ZSTAT [ECB|POOL|CPU|IO|ALL]",
        "description": "Displays real-time z/TPF system performance metrics including ECB utilization, core block levels, I/O rates, and CPU consumption per processor.",
        "output_fields": [
            "ECB UTILIZATION: nn%",
            "CORE BLOCKS FREE: nnnnn",
            "TRANSACTIONS/SEC: nnnn",
            "CPU TIME USED: nn.nn%",
            "DISK I/O RATE: nnnn/SEC",
        ],
        "example": "ZSTAT ALL",
        "category": "Performance",
    },
    "ZECB": {
        "purpose": "ECB Control and Display",
        "syntax": "ZECB [DISPLAY|TRACE|ALTER] ecb_addr",
        "description": "Display or alter the contents of active Entry Control Blocks. Can start/stop tracing on specific ECBs for debugging. Shows ECB state, program chain, and data levels.",
        "output_fields": [
            "ECB ADDR: xxxxxxxx",
            "STATE: ACTIVE/SUSPENDED/WAITING",
            "CURRENT PROGRAM: XXXXXXXX",
            "ENTRY: XXXXX SEG: XX",
            "PRIORITY: nn",
        ],
        "example": "ZECB DISPLAY 0A3F00",
        "category": "Diagnostic",
    },
    "ZTRAP": {
        "purpose": "Diagnostic Software Trap",
        "syntax": "ZTRAP SET|DELETE|DISPLAY entry [SEG segment] [ADDR offset]",
        "description": "Set, display, or delete software traps to intercept program execution for debugging. When an ECB hits the trap address, execution is suspended and a dump is taken.",
        "output_fields": [
            "TRAP SET AT: ENTRY=XXXXX SEG=XX OFFSET=xxxx",
            "TRAP STATUS: ACTIVE/INACTIVE",
            "HIT COUNT: nnn",
        ],
        "example": "ZTRAP SET TR001 SEG 00 ADDR 0050",
        "category": "Diagnostic",
    },
    "ZDUMP": {
        "purpose": "Memory Dump",
        "syntax": "ZDUMP ecb_addr|ALL [CORE|FILE|FULL]",
        "description": "Captures the contents of memory for a specific ECB or system area. Output includes all data levels, registers, PSW, and program chain for post-mortem analysis.",
        "output_fields": [
            "DUMP TAKEN AT: timestamp",
            "ECB ADDR: xxxxxxxx",
            "ALL DATA LEVELS D0-DF",
            "PROGRAM CHAIN",
            "ALL REGISTERS GR0-GR15",
        ],
        "example": "ZDUMP 0A3F00 FULL",
        "category": "Diagnostic",
    },
    "ZPOOL": {
        "purpose": "Storage Pool Status",
        "syntax": "ZPOOL [STATUS|DETAIL|ecb_level]",
        "description": "Display the status of z/TPF core storage pools including available blocks, peak usage, and allocation rates. Critical for detecting memory leaks (GETCC without RELCC).",
        "output_fields": [
            "POOL NAME: CE1CR0 / CExxxx",
            "BLOCKS FREE: nnnnn",
            "BLOCKS USED: nnnnn",
            "PEAK USAGE: nnnnn",
            "ALLOC RATE: nnn/SEC",
        ],
        "example": "ZPOOL STATUS",
        "category": "Storage",
    },
    "ZINET": {
        "purpose": "Internet / TCP-IP Daemon Control",
        "syntax": "ZINET [START|STOP|DISPLAY] [daemon_name]",
        "description": "Manages z/TPF TCP/IP sockets, starts/stops daemons (HTTP, FTP, SMTP), and displays active network connections and daemon status.",
        "output_fields": [
            "DAEMON: HTTP  STATUS: ACTIVE  PORT: 80",
            "CONNECTIONS: nnn ACTIVE",
            "BYTES RECV: nnnnnnnn",
            "BYTES SENT: nnnnnnnn",
        ],
        "example": "ZINET DISPLAY HTTP",
        "category": "Network",
    },
    "ZMQSC": {
        "purpose": "WebSphere MQ Control",
        "syntax": "ZMQSC [DISPLAY|START|STOP] [queue_manager]",
        "description": "Manage WebSphere MQ queue managers, queues, and channels on z/TPF. Display message depth, channel status, and connection counts.",
        "output_fields": [
            "QMGR: QMNAME  STATUS: RUNNING",
            "QUEUE: QNAME  DEPTH: nnn  MAX: nnnn",
            "CHANNEL: CHNAME  STATUS: RUNNING",
        ],
        "example": "ZMQSC DISPLAY QMGR1",
        "category": "Messaging",
    },
    "ZTPFDF": {
        "purpose": "TPFDF Database Management",
        "syntax": "ZTPFDF [DISPLAY|ADD|DELETE|MODIFY] [db_name]",
        "description": "Create, display, and manage TPFDF (TPF Database Facility) databases and structures. Manage table definitions, indexes, and data organization.",
        "output_fields": [
            "DB NAME: xxxxxxxx  STATUS: ACTIVE",
            "RECORDS: nnnnnnnn",
            "INDEX STATUS: VALID/REBUILDING",
            "SPACE USED: nnnnK",
        ],
        "example": "ZTPFDF DISPLAY PNRDB",
        "category": "Database",
    },
    "ZPROG": {
        "purpose": "Program Load/Status Control",
        "syntax": "ZPROG [LOAD|DELETE|DISPLAY] program_name",
        "description": "Display program attributes, load status, and core residency. Load or delete application programs dynamically without system IPL.",
        "output_fields": [
            "PROGRAM: XXXXXXXX  STATUS: LOADED/NOT LOADED",
            "CORE ADDRESS: xxxxxxxx",
            "SIZE: nnnnnK",
            "LOAD DATE: DD/MM/YY HH:MM:SS",
            "ECB COUNT USING: nnn",
        ],
        "example": "ZPROG DISPLAY TR001",
        "category": "Program",
    },
    "ZLOG": {
        "purpose": "System Log Control",
        "syntax": "ZLOG [DISPLAY|START|STOP|CLEAR] [filter]",
        "description": "Display or control the logging of system messages. Filter by message ID, severity, or program. Essential for monitoring and troubleshooting.",
        "output_fields": [
            "LOG STATUS: ACTIVE",
            "MSG COUNT: nnnnnnn",
            "LAST MSG: timestamp  ID: xxxxxxxx",
        ],
        "example": "ZLOG DISPLAY ERR",
        "category": "Logging",
    },
}

# ─── COMPREHENSIVE z/TPF SYSTEM KNOWLEDGE FOR CHAT ───
ZTPF_SYSTEM_KNOWLEDGE = {
    "overview": """
IBM z/TPF (Transaction Processing Facility) is a high-throughput, real-time
operating system designed for ultra-high volume transaction processing, primarily
in the airline and financial services industries. It can process millions of
transactions per second with sub-millisecond response times.

Key characteristics:
- Non-preemptive, cooperative multitasking via ECBs
- Direct hardware access (no virtual memory overhead in critical paths)
- Persistent 'always-on' execution model (no process startup overhead)
- Supports millions of concurrent sessions (e.g., airline reservation systems)
""",

    "ecb": """
The Entry Control Block (ECB) is the fundamental unit of execution in z/TPF.
Think of it as a lightweight transaction context (similar to a thread/coroutine).

ECB Structure:
- Data Levels D0-DF: 16 addressable 4KB storage areas per ECB
- CE1CR0: Communication Register 0 — input data area (request message)
- CE1CR4: Communication Register 4 — flags and control
- Registers GR0-GR15: Standard System/390 general-purpose registers

ECB Lifecycle:
1. ECB is dispatched when a transaction arrives (terminal/network)
2. Program chain executes: ENTER → program1 → ENTER → program2 → EXITC
3. EXITC or EXITN terminates the ECB and releases resources
4. Files/locks held by FIWHC must be released with UNFRC before EXITC
""",

    "var_file": """
VAR (Variable Definition) File — IBM z/TPF Engineering Artifact

The VAR file defines ALL variables used in a z/TPF transaction entry.
It is a fixed-width column document used for code review and documentation.

FORMAT:
═══════════════════════════════════════════════════════════════════════════
VAR NAME         TYPE    LEN  SOURCE       DEFAULT     VALIDATION    DESCRIPTION
═══════════════════════════════════════════════════════════════════════════
ERR_CODE         BIN     2    INTERNAL     X'0000'     0-9999        Error return code
RET_CODE         BIN     2    INTERNAL     X'0000'     0-9999        Function return code
ECB_PTR          ADDR    4    ECB          N/A         NON-NULL      ECB base address
INPUT_DATA       CHAR    8    CE1CR0+0     SPACES      NON-BLANK     Input PNR/key field
FILE_REC_PTR     ADDR    4    FILE         N/A         N/A           Pointer to file record
PROCESS_FLAG     BIN     1    INTERNAL     X'00'       X'00'-X'FF'   Processing control flag
═══════════════════════════════════════════════════════════════════════════

Types: CHAR (character), BIN (binary), PACK (packed decimal), HEX (hex constant),
       ADDR (address pointer), EQU (equate/constant)
Sources: INPUT (from terminal/network), FILE (from z/TPF file system),
         SYSTEM (system macro output), INTERNAL (program-generated),
         ECB (from ECB data level), COMPUTED (calculated value)
""",

    "tdr": """
TDR (Transaction Design Record) — IBM z/TPF Engineering Document

The TDR is the primary requirements and design document for a z/TPF transaction.
It defines what the entry does, how it does it, and how to monitor/debug it.

STANDARD TDR FORMAT:
════════════════════════════════════════════
TDR NAME:        TR001-DISPLAY-PNR
ENTRY NAME:      TR001
SEGMENT:         00
VERSION:         1.0
DATE:            2026-05-13
AUTHOR:          STS Coder AI

PURPOSE:
  Receives a PNR (Passenger Name Record) display request from a travel agent
  terminal. Retrieves the PNR record from the z/TPF file system and formats
  the response for display.

INPUT FIELDS:
  Offset 0-7:   PNR Locator (8 bytes, CHAR)
  Offset 8:     Request Type (1 byte, BIN) 00=Display, 01=List

OUTPUT FIELDS:
  Offset 0-3:   Return Code (BIN, 0=Success)
  Offset 4-7:   Record Count (BIN)
  Offset 8-n:   Formatted PNR Data

DEPENDENCIES:
  Macros: ENTER, FINDA, FILEC, GETCC, RELCC, EXITC, EXITN
  Files:  PNRDB (TPFDF PNR Database)

EXCEPTIONS:
  RC=4:  PNR Not Found (FINDA failure)
  RC=8:  File System Error (FILEC failure)
  RC=12: Storage Allocation Failure (GETCC failure)
  RC=16: Invalid Input (validation failure)

Z COMMANDS FOR MONITORING:
  ZDECB  — Dump ECB data after failure
  ZTRAP  — Set trap on entry for debugging
  ZDUMP  — Full memory dump for post-mortem
  ZECB   — Display active ECBs for this entry
  ZTPFDF — Check PNRDB database status
  ZSTAT  — Monitor system performance impact

REXX/RAVEN INTERFACE:
  RAVEN exec TR001MON can monitor this entry.
  Use: ADDRESS RAVEN 'DISPLAY ECB TR001'
════════════════════════════════════════════
""",

    "tdrv": """
TDRV (Test Driver) File — IBM z/TPF Engineering Artifact

The TDRV defines the step-by-step processing flow of a transaction entry.
It is used for test planning, code walkthrough, and documentation.

STANDARD TDRV FORMAT:
═══════════════════════════════════════════════════════════════════════════════════
STEP  ACTION                    ENTRY      CONDITION              NEXT
═══════════════════════════════════════════════════════════════════════════════════
001   RECEIVE REQUEST           TR001      ECB dispatched         002
002   VALIDATE INPUT            TR001      CE1CR0 non-blank       003 / ERR-001
003   ALLOCATE STORAGE          TR001      GETCC CE1CR0 level     004 / ERR-002
004   FILE ACCESS - READ        TR001      FINDA PNRDB by key     005 / ERR-003
005   PROCESS DATA              TR001      Record found           006
006   FORMAT OUTPUT             TR001      Data valid             007
007   RETURN RESPONSE           TR001      RC=0 success           EXIT
ERR-001 ERROR HANDLING          TR001      Invalid input RC=16    EXIT-ERR
ERR-002 ERROR HANDLING          TR001      GETCC failed RC=12     EXIT-ERR
ERR-003 ERROR HANDLING          TR001      FINDA failed RC=4      EXIT-ERR
EXIT    EXITC                   TR001      Normal completion      -
EXIT-ERR EXITN                  TR001      Error completion       -
═══════════════════════════════════════════════════════════════════════════════════
""",

    "rexx_raven": """
IBM z/TPF REXX / RAVEN — Complete Guide

RAVEN (Real-time Automation and Verification ENvironment) is the z/TPF
Operations Server REXX execution environment for automation, monitoring,
and operational scripting.

─── BASIC REXX/RAVEN TEMPLATE ───────────────────────────────────────────────
/* REXX - IBM z/TPF RAVEN Exec */
/* Exec Name: MONTR001                                                       */
/* Purpose:   Monitor TR001 entry and alert on errors                        */
/* Author:    STS Coder AI                                                   */

ADDRESS RAVEN              /* Set RAVEN as command environment */

PARSE ARG entry_name threshold

IF entry_name = '' THEN DO
  SAY 'ERROR: Entry name required'
  EXIT 8
END

/* Issue z/TPF operator command and capture output */
'ZSTAT ECB'
rc_stat = RC
IF rc_stat \= 0 THEN DO
  SAY 'WARNING: ZSTAT failed, RC='rc_stat
END

/* Check program status */
'ZPROG DISPLAY' entry_name
IF RC = 0 THEN
  SAY entry_name 'is LOADED and active'
ELSE DO
  SAY 'ALERT:' entry_name 'is NOT LOADED - RC='RC
  EXIT 4
END

/* Set a diagnostic trap if threshold exceeded */
'ZTRAP SET' entry_name 'SEG 00 ADDR 0000'
IF RC = 0 THEN
  SAY 'Trap set on' entry_name

EXIT 0
─────────────────────────────────────────────────────────────────────────────

Key RAVEN Rules:
1. ADDRESS RAVEN must be first command environment set
2. All z/TPF operator commands go through RAVEN: 'ZDSYS ALL'
3. Always check RC (return code) after every command
4. PARSE ARG is used to receive arguments
5. Use SAY for console output in RAVEN execs
6. EXIT with non-zero code on errors for automation monitoring
7. Avoid CALL DELAY — use RAVEN timing functions instead
8. Use /* REXX */ comment on first line (required)
""",

    "macros": """
IBM z/TPF Core Macros — Complete Reference

═══ LIFECYCLE MACROS ═══════════════════════════════════════════════
ENTER   — Transfer control to another program
          ENTER TRDR     (enter entry TRDR)
          ENTER TRDR,D=1 (enter with data level 1)

EXITC   — Normal ECB termination, release resources
          EXITC         (terminate, send response)
          EXITC NOTERM  (terminate, no response)

EXITN   — Error ECB termination
          EXITN         (terminate on error, no response)

BACKC   — Return to calling program (reverse of ENTER)
          BACKC         (return to caller)

═══ FILE ACCESS MACROS ══════════════════════════════════════════════
FINDA   — Find/Read a record into ECB level
          FINDA CE1CR0,KEY=(R3),FILE=PNRDB

FILEC   — Write a record to the file system
          FILEC CE1CR0,FILE=PNRDB,TYPE=UPDATE

FIWHC   — Lock a file record (exclusive hold)
          FIWHC CE1CR0,FILE=PNRDB

UNFRC   — Release a held file record (MUST follow FIWHC before EXITC)
          UNFRC CE1CR0

═══ STORAGE MACROS ══════════════════════════════════════════════════
GETCC   — Allocate a working storage core block
          GETCC CE1CR0,LV=1 (allocate at data level 1)

RELCC   — Release an allocated core block (MUST pair with GETCC)
          RELCC CE1CR0,LV=1

GLOBZ   — Access global (shared) storage area
          GLOBZ AREA=SHARED

═══ COMMUNICATION MACROS ════════════════════════════════════════════
SERVC   — Synchronous service call
          SERVC FUNC=TIMER,TIME=100

CRUSA   — Get record using search argument
CRUSC   — Continue search from prior CRUSA

═══ CRITICAL RULES ══════════════════════════════════════════════════
1. Every FIWHC MUST have a matching UNFRC before EXITC/EXITN
2. Every GETCC MUST have a matching RELCC before EXITC/EXITN  
3. Never branch into another CSECT — use ENTER/BACKC
4. Programs must be REENTRANT — no self-modification
5. Data areas cannot reside in the program CSECT
""",
}

# ─── CHAT TOPIC ROUTER ───
# Maps user query keywords to knowledge topics
CHAT_TOPICS = {
    "ecb": "ecb",
    "entry control block": "ecb",
    "var file": "var_file",
    "var": "var_file",
    "variable definition": "var_file",
    "tdr": "tdr",
    "transaction design": "tdr",
    "tdrv": "tdrv",
    "test driver": "tdrv",
    "rexx": "rexx_raven",
    "raven": "rexx_raven",
    "macro": "macros",
    "macros": "macros",
    "finda": "macros",
    "filec": "macros",
    "enter": "macros",
    "exitc": "macros",
    "getcc": "macros",
    "relcc": "macros",
    "fiwhc": "macros",
    "unfrc": "macros",
    "overview": "overview",
    "what is tpf": "overview",
    "what is ztpf": "overview",
    "z/tpf": "overview",
}

# ─── MERGED KNOWLEDGE DICT (for backward compat) ───
KNOWLEDGE = {
    "conventions": [
        "z/TPF application programs must be strictly reentrant — they cannot modify their own instruction streams.",
        "A standard basic entry cannot exceed 4KB; generalized objects may be up to 64KB.",
        "Never hold FIWHC (file locks) across DLAYC or defer macros.",
        "Always use ENTER/EXITC/BACKC for program linkage — never branch across CSECTs.",
        "Data definitions must reside in the data area, not the program CSECT.",
        "Every GETCC must be paired with a RELCC before EXITC.",
        "Every FIWHC must be paired with an UNFRC before EXITC.",
    ],
    "macros": {
        "ENTER":  "Transfers control to another z/TPF program. Format: ENTER TRDR",
        "EXITC":  "Terminates ECB normally and releases resources. Format: EXITC",
        "EXITN":  "Terminates ECB on error, no response sent. Format: EXITN",
        "BACKC":  "Returns to the calling program that issued ENTER.",
        "FILEC":  "Writes a record to the z/TPF file system.",
        "FINDA":  "Reads a record into the specified ECB data level.",
        "FIWHC":  "Locks a file record exclusively (must be released with UNFRC).",
        "UNFRC":  "Releases a FIWHC-held file record.",
        "GETCC":  "Allocates a working storage core block at specified ECB level.",
        "RELCC":  "Releases a GETCC-allocated storage block.",
        "GLOBZ":  "Accesses global shared storage areas.",
        "CRUSA":  "Gets records using a search argument.",
        "CRUSC":  "Continues a search from a prior CRUSA.",
        "SERVC":  "Issues a synchronous z/TPF system service call.",
    },
    "rexx_raven": [
        "ADDRESS RAVEN sets the RAVEN execution environment for z/TPF operator commands.",
        "All exec files must begin with /* REXX */ on the first line.",
        "PARSE ARG receives command-line arguments in RAVEN execs.",
        "Always check RC (return code) after every z/TPF command issued via RAVEN.",
        "Use SAY for console output in RAVEN automation scripts.",
        "Avoid blocking calls in REXX — use RAVEN timing/async functions instead.",
        "RAVEN execs run in the Operations Server environment, not the z/TPF main system.",
        "Issue z/TPF commands by enclosing them in quotes: 'ZDSYS ALL'",
        "Use EXIT 0 for success, EXIT 4 for warnings, EXIT 8 for errors.",
    ],
    "z_commands": {cmd: info["purpose"] + ". " + info["description"]
                   for cmd, info in ZCMD_RESPONSES.items()},
    "ecb_processing": [
        "The Entry Control Block (ECB) is the primary dispatching unit in z/TPF.",
        "Each ECB has 16 data levels (D0-DF), each holding a 4KB core block.",
        "CE1CR0 is the primary input communication register holding the transaction request.",
        "CE1CR4 holds ECB control flags and processing indicators.",
        "An ECB can be suspended for I/O and resumes when the resource is available.",
        "EXITC terminates normally; EXITN terminates on error; BACKC returns to caller.",
        "File locks (FIWHC) and storage (GETCC) MUST be released before EXITC.",
    ],
    "advisor_troubleshooting": {
        "ECB_RESOURCE_LOCKOUT": "If ECB is hanging — check active ECBs with ZECB or ZDECB. Verify FIWHC has matching UNFRC.",
        "MEMORY_LEAK": "If GETCC used without RELCC — check core depletion with ZPOOL and ZSTAT.",
        "NETWORK_HANG": "For socket/TCP issues — use ZINET and ZDTCP to display connections.",
        "SYSTEM_CRASH": "For CTL-dumps — set ZTRAP on entry and analyze with ZDUMP.",
        "PERFORMANCE": "For slow entries — use ZMEAS and ZSTAT for CPU/IO profiling.",
    },
    "advisor_guidance": [
        "Always suggest Z-Commands to operators for monitoring: ZECB, ZTRAP, ZSTAT, ZDUMP.",
        "Flag any FIWHC without UNFRC as a critical ERROR.",
        "Flag any GETCC without RELCC as a WARNING for storage leak.",
        "Recommend ZTPFDF for database access patterns.",
        "For REXX execs, always recommend checking RC after each command.",
    ],
    "system_knowledge": ZTPF_SYSTEM_KNOWLEDGE,
    "zcmd_detail": ZCMD_RESPONSES,
    "chat_topics": CHAT_TOPICS,
}
