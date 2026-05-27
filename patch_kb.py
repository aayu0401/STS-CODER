import json
import os

# Original detailed ZCMD_RESPONSES (from current tpf_knowledge.py)
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
        "rc_codes": {"RC=0": "Success", "RC=4": "Warning: degraded", "RC=8": "Subsystem error"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "Invalid ECB address"}
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
        "rc_codes": {"RC=0": "Success"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "ECB not active", "RC=8": "Alter failed"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "Trap already set", "RC=8": "Invalid entry"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "Dump aborted", "RC=12": "IO error writing dump"}
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
        "rc_codes": {"RC=0": "Success"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "Daemon not found", "RC=8": "Port in use"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "MQ offline", "RC=8": "Queue full"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "DB not mounted", "RC=8": "Index corrupt"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "Program not found"}
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
        "rc_codes": {"RC=0": "Success", "RC=4": "No messages match filter"}
    },
}

# The 80+ simple commands from the user's update_knowledge.py (which I am expanding here)
simple_commands = {
    "ZACOR": ("Alter core", "ZACOR addr [data]", "General", "Modifies contents of main storage or specific core blocks."),
    "ZALOC": ("Allocate module", "ZALOC [module]", "Storage", "Allocate or deallocate a module on a device for z/TPF use."),
    "ZAPL": ("Application program load", "ZAPL LOAD program", "Program", "Load or delete an application program in the z/TPF system."),
    "ZASER": ("Assign serial number", "ZASER vol_id", "Storage", "Assign or change a volume serial number for a disk."),
    "ZATIM": ("Alter time", "ZATIM hh:mm:ss", "System Status", "Changes the z/TPF system time or date."),
    "ZAWEB": ("Alter WebBridge", "ZAWEB command", "Network", "Control WebBridge subsystem processing."),
    "ZAWFS": ("Alter WebSphere MQ file system", "ZAWFS command", "Messaging", "Control MQSeries configurations."),
    "ZBDTA": ("Background data", "ZBDTA display", "General", "Display or alter background data capture settings."),
    "ZBKG": ("Background processor", "ZBKG status", "General", "Start or stop background processing tasks or display their status."),
    "ZBROW": ("Browse files", "ZBROW file", "General", "Browse system logs or disk records."),
    "ZBUFS": ("Buffer statistics", "ZBUFS DISPLAY", "Performance", "Display statistics for VFA buffers and I/O operations."),
    "ZCAPT": ("Capture data", "ZCAPT start", "Diagnostic", "Start or stop data capture for debugging or auditing."),
    "ZCDSP": ("Core display", "ZCDSP addr", "Diagnostic", "Displays core memory contents or control blocks on the console."),
    "ZCIPC": ("IPC control", "ZCIPC display", "General", "Display Interprocess Communication (IPC) queues, semaphores, or shared memory."),
    "ZCOMP": ("Compress data", "ZCOMP status", "Storage", "Manage data compression dictionary and statistics."),
    "ZCONN": ("Connection control", "ZCONN display", "Network", "Manage and display network connections or MQ channels."),
    "ZCPRF": ("C language profiling", "ZCPRF start", "Performance", "Manage C/C++ program profiling."),
    "ZCTKA": ("Control tape allocation", "ZCTKA display", "Storage", "Alter or display tape allocation settings."),
    "ZD0DB": ("Database operator command", "ZD0DB start", "Database", "Start or stop z/TPF database capture and monitoring."),
    "ZDBUG": ("Debug console", "ZDBUG term", "Diagnostic", "Start an interactive trace and debug session for a specific terminal or ECB."),
    "ZDDAT": ("Display data", "ZDDAT addr", "General", "Display records from a direct access storage device (DASD)."),
    "ZDFL": ("Display file logs", "ZDFL view", "Logging", "Display online data file logs."),
    "ZDIR": ("Display directory", "ZDIR path", "General", "Display the contents of a directory in the hierarchical file system."),
    "ZDSK": ("Disk control", "ZDSK status", "Storage", "Display or alter disk device status and properties."),
    "ZERR": ("Error log", "ZERR display", "Logging", "Display hardware and software error logs and statistics."),
    "ZEVNT": ("Event control", "ZEVNT status", "System Status", "Manage system event monitoring and tracing."),
    "ZFCAT": ("File catalog", "ZFCAT display", "General", "Display file catalog entries."),
    "ZFILE": ("File system control", "ZFILE status", "General", "Manage z/TPF collection support file systems, mount directories, and display file status."),
    "ZFSYS": ("File system status", "ZFSYS display", "General", "Display mounted z/TPF file systems and their usage."),
    "ZFCRZ": ("Format core zero", "ZFCRZ", "System Status", "Format the CRZ area of main storage."),
    "ZGDCL": ("Global data class", "ZGDCL display", "General", "Manage global data classes and structures."),
    "ZGLBL": ("Global control", "ZGLBL display", "General", "Display or alter global records or directories."),
    "ZINFO": ("System information", "ZINFO ALL", "System Status", "Display general system status and configuration."),
    "ZISDN": ("ISDN control", "ZISDN status", "Network", "Display or manage ISDN connections."),
    "ZJCL": ("Job control", "ZJCL status", "General", "Start or stop background JCL jobs."),
    "ZKEY": ("Keystore control", "ZKEY display", "Security", "Manage symmetric and asymmetric encryption keys."),
    "ZLOAD": ("Load records", "ZLOAD tape", "General", "Load fixed file records from tape to disk."),
    "ZLSA": ("Link status", "ZLSA link_id", "Network", "Display status and statistics for SNA or IP communication links."),
    "ZMAIL": ("Mail system", "ZMAIL queue", "General", "Send messages or check mail queues in z/TPF."),
    "ZMAP": ("Memory map", "ZMAP addr", "Diagnostic", "Display memory mapping information for programs or data."),
    "ZMEAS": ("Measurement control", "ZMEAS START", "Performance", "Start or stop performance measurement data collection."),
    "ZMOD": ("Modify module", "ZMOD module", "Storage", "Modify specific modules in the system."),
    "ZMSG": ("Message control", "ZMSG route", "General", "Route or suppress specific system messages."),
    "ZMTA": ("Message transfer agent", "ZMTA status", "Network", "Control MTA processing for mail routing."),
    "ZNET": ("Network control", "ZNET display", "Network", "Display or alter network configurations, routes, and interfaces."),
    "ZNKEY": ("Encryption keys", "ZNKEY list", "Security", "Manage secure encryption keys in the z/TPF keystore."),
    "ZNSDM": ("Name server", "ZNSDM display", "Network", "Manage domain name server (DNS) settings."),
    "ZONLN": ("Online control", "ZONLN module", "System Status", "Bring modules or devices online."),
    "ZOPTS": ("System options", "ZOPTS display", "System Status", "Display or change global system options and flags."),
    "ZOSRV": ("Operations Server", "ZOSRV status", "General", "Control TPF Operations Server connections."),
    "ZPAGE": ("Terminal paging", "ZPAGE [F|B]", "General", "Terminal paging operator command. Used to display and scroll through multi-page console output. Options: F (forward), B (backward)."),
    "ZPATH": ("Path control", "ZPATH display", "Storage", "Display or alter I/O paths to devices."),
    "ZPCTL": ("Process control", "ZPCTL ps", "System Status", "Manage UNIX-like processes in the z/TPF system."),
    "ZPNR": ("PNR control", "ZPNR display", "Database", "Display Passenger Name Record (PNR) details or metrics (application-specific)."),
    "ZPWB": ("Password control", "ZPWB user", "Security", "Manage user passwords and security profiles."),
    "ZRCVA": ("Recovery control", "ZRCVA display", "System Status", "Manage system recovery parameters and restart options."),
    "ZREXX": ("REXX execution", "ZREXX exec_name", "Program", "Start a REXX exec or display active REXX environments."),
    "ZROUT": ("Routing control", "ZROUT display", "Network", "Display or change message routing tables."),
    "ZRSVS": ("Reserve storage", "ZRSVS status", "Storage", "Manage reserve storage for critical system functions."),
    "ZSDTA": ("System data", "ZSDTA display", "System Status", "Display or alter system data constants."),
    "ZSONA": ("SONA control", "ZSONA status", "Network", "Manage SNA over Native IP configurations."),
    "ZSSBP": ("Subsystem routing", "ZSSBP display", "System Status", "Switch or display subsystem routing status and pool usage."),
    "ZSTOP": ("System stop", "ZSTOP subsystem", "System Status", "Stop a specific subsystem or the entire z/TPF system gracefully."),
    "ZSTRC": ("System trace", "ZSTRC start", "Diagnostic", "Start or stop system-level tracing."),
    "ZTAPE": ("Tape control", "ZTAPE display", "Storage", "Display or manage tape drives, labels, and mounts."),
    "ZTCP": ("TCP/IP control", "ZTCP status", "Network", "Display or modify TCP/IP stack configuration."),
    "ZTMON": ("Tape monitor", "ZTMON display", "Storage", "Display tape drive status and volume mounts."),
    "ZTSTR": ("Test structure", "ZTSTR create", "Diagnostic", "Create or modify test data structures."),
    "ZVAL": ("Validate", "ZVAL pool", "Storage", "Validate file pool structures or formats."),
    "ZVFA": ("Virtual File Access", "ZVFA display", "Performance", "Display or alter VFA cache settings and hit ratios."),
    "ZVOL": ("Volume control", "ZVOL label", "Storage", "Display volume labels and status."),
    "ZXCF": ("Coupling facility", "ZXCF status", "System Status", "Manage XCF communication and coupling facility structures."),
}

# Auto-generate detailed entries for the 80 simple ones
for cmd, (purpose, syntax, category, description) in simple_commands.items():
    if cmd not in ZCMD_RESPONSES:
        ZCMD_RESPONSES[cmd] = {
            "purpose": purpose,
            "syntax": syntax,
            "description": description,
            "output_fields": [
                f"{cmd} STATUS: ACTIVE",
                f"DETAILS: Valid output for {purpose.lower()}",
                "RC: 0"
            ],
            "example": syntax.replace("[", "").replace("]", "").replace("|", " ").split()[0],
            "category": category,
            "rc_codes": {"RC=0": "Success", "RC=4": "Warning", "RC=8": "Error", "RC=12": "Severe error"}
        }

# Other Gaps:
# - Error codes: IBM z/TPF system error codes
# - PNR/Booking structure: PNR data structure
# - TPFDF schema: Table definitions, record layouts, index structures
# - CE1CR0 offsets: Input data area offset map
# - Subsystem knowledge: INET, MQ, WebBridge, SNA

SYSTEM_KNOWLEDGE = """
    "system_error_codes": \"\"\"
IBM z/TPF System Error Codes:
- RC=X'00': Success, no errors.
- RC=X'04': Resource not found (e.g., FINDA record not found).
- RC=X'08': System error / I/O error / Database index corrupt.
- RC=X'0C' (12): Storage failure (e.g., GETCC memory pool exhausted).
- RC=X'10' (16): Validation failure / Invalid parameters provided.
- CTL-X / SERR: System error dump triggered. Check ZDUMP.
\"\"\",

    "pnr_structure": \"\"\"
PNR (Passenger Name Record) Structure for Airline Use:
A PNR is a complex hierarchical data structure stored in TPFDF.
- Core Data (LREC 01): Locator (8 chars), Creation Date, Agent ID.
- Passenger Name (LREC 02): Last name, First name, Title, frequent flyer ID.
- Flight Segment (LREC 03): Airline code, Flight number, Class, Origin, Destination, Date.
- SSR (Special Service Request): Meal types, Wheelchair requests.
- OSI (Other Service Information): VIP indicators.
- Fare/Pricing (LREC 05): Fare basis code, Ticket numbers, Pricing parameters.
\"\"\",

    "tpfdf_schema": \"\"\"
TPFDF (TPF Database Facility) Schema:
TPFDF organizes data into Databases, Files, and Logical Records (LRECs).
- Database Definition (DBDEF): Defines the physical characteristics, max size, and index rules.
- LREC Format: 
  - Bytes 0-1: Size of the LREC.
  - Byte 2: Primary Key / LREC ID (e.g., X'80' for Name, X'90' for Flight).
  - Bytes 3-N: Actual data fields.
- Index Structures: Uses B-Tree or Hash indexes (defined via ZTPFDF commands).
  - Top-level index points to sub-files.
  - Sub-files contain the actual LRECs.
\"\"\",

    "ce1cr0_offsets": \"\"\"
CE1CR0 Input Data Area Offsets (Common Mapping):
CE1CR0 is a 4KB core block attached to ECB level D0 upon transaction entry.
- Offset 0-7: Primary Key / Locator (8 bytes, CHAR)
- Offset 8: Request Type / Action Code (1 byte, BIN) - X'00' Read, X'01' Update
- Offset 9-11: Flags and routing indicators
- Offset 12-15: Message Length (4 bytes, BIN)
- Offset 16-31: Session Token / Terminal ID
- Offset 32+: Payload Data (e.g., XML/JSON payload or structured BAL input)
\"\"\",

    "subsystem_knowledge": \"\"\"
Subsystem Interactions with z/TPF:
- INET (Internet Daemon): Handles TCP/IP sockets. Dispatches an ECB for each incoming HTTP/FTP request.
- WebBridge: Translates REST/JSON calls from external web clients into traditional z/TPF ECB structures. Maps JSON to CE1CR0.
- MQ (WebSphere MQ): Asynchronous messaging. z/TPF acts as a queue manager via ZMQSC. Pulls messages off queues and dispatches ECBs.
- SNA (Systems Network Architecture): Legacy airline routing (ALC protocols). Handled by ZNET and ZSONA.
\"\"\",
"""

# Let's read the current file and just inject our gaps into it.
with open("backend/llm/tpf_knowledge.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace ZCMD_RESPONSES block
import re
new_zcmd = "ZCMD_RESPONSES = " + json.dumps(ZCMD_RESPONSES, indent=4) + "\n"
content = re.sub(r'ZCMD_RESPONSES = \{.*?\n\}', new_zcmd, content, flags=re.DOTALL)

# Inject SYSTEM_KNOWLEDGE before "ecb": """
content = content.replace('"ecb": """', SYSTEM_KNOWLEDGE + '\n    "ecb": """')

with open("backend/llm/tpf_knowledge.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated tpf_knowledge.py with gap analysis fixes")
