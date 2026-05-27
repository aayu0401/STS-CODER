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
            "XPC STATUS: CONNECTED/DISCONNECTED"
        ],
        "example": "ZDSYS ALL",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "Warning: degraded",
            "RC=8": "Subsystem error"
        }
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
            "PROGRAM STATUS WORD (PSW)"
        ],
        "example": "ZDECB 0A3F00 D0 HEX",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "Invalid ECB address"
        }
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
            "DISK I/O RATE: nnnn/SEC"
        ],
        "example": "ZSTAT ALL",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success"
        }
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
            "PRIORITY: nn"
        ],
        "example": "ZECB DISPLAY 0A3F00",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "ECB not active",
            "RC=8": "Alter failed"
        }
    },
    "ZTRAP": {
        "purpose": "Diagnostic Software Trap",
        "syntax": "ZTRAP SET|DELETE|DISPLAY entry [SEG segment] [ADDR offset]",
        "description": "Set, display, or delete software traps to intercept program execution for debugging. When an ECB hits the trap address, execution is suspended and a dump is taken.",
        "output_fields": [
            "TRAP SET AT: ENTRY=XXXXX SEG=XX OFFSET=xxxx",
            "TRAP STATUS: ACTIVE/INACTIVE",
            "HIT COUNT: nnn"
        ],
        "example": "ZTRAP SET TR001 SEG 00 ADDR 0050",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "Trap already set",
            "RC=8": "Invalid entry"
        }
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
            "ALL REGISTERS GR0-GR15"
        ],
        "example": "ZDUMP 0A3F00 FULL",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "Dump aborted",
            "RC=12": "IO error writing dump"
        }
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
            "ALLOC RATE: nnn/SEC"
        ],
        "example": "ZPOOL STATUS",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success"
        }
    },
    "ZINET": {
        "purpose": "Internet / TCP-IP Daemon Control",
        "syntax": "ZINET [START|STOP|DISPLAY] [daemon_name]",
        "description": "Manages z/TPF TCP/IP sockets, starts/stops daemons (HTTP, FTP, SMTP), and displays active network connections and daemon status.",
        "output_fields": [
            "DAEMON: HTTP  STATUS: ACTIVE  PORT: 80",
            "CONNECTIONS: nnn ACTIVE",
            "BYTES RECV: nnnnnnnn",
            "BYTES SENT: nnnnnnnn"
        ],
        "example": "ZINET DISPLAY HTTP",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "Daemon not found",
            "RC=8": "Port in use"
        }
    },
    "ZMQSC": {
        "purpose": "WebSphere MQ Control",
        "syntax": "ZMQSC [DISPLAY|START|STOP] [queue_manager]",
        "description": "Manage WebSphere MQ queue managers, queues, and channels on z/TPF. Display message depth, channel status, and connection counts.",
        "output_fields": [
            "QMGR: QMNAME  STATUS: RUNNING",
            "QUEUE: QNAME  DEPTH: nnn  MAX: nnnn",
            "CHANNEL: CHNAME  STATUS: RUNNING"
        ],
        "example": "ZMQSC DISPLAY QMGR1",
        "category": "Messaging",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "MQ offline",
            "RC=8": "Queue full"
        }
    },
    "ZTPFDF": {
        "purpose": "TPFDF Database Management",
        "syntax": "ZTPFDF [DISPLAY|ADD|DELETE|MODIFY] [db_name]",
        "description": "Create, display, and manage TPFDF (TPF Database Facility) databases and structures. Manage table definitions, indexes, and data organization.",
        "output_fields": [
            "DB NAME: xxxxxxxx  STATUS: ACTIVE",
            "RECORDS: nnnnnnnn",
            "INDEX STATUS: VALID/REBUILDING",
            "SPACE USED: nnnnK"
        ],
        "example": "ZTPFDF DISPLAY PNRDB",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "DB not mounted",
            "RC=8": "Index corrupt"
        }
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
            "ECB COUNT USING: nnn"
        ],
        "example": "ZPROG DISPLAY TR001",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "Program not found"
        }
    },
    "ZLOG": {
        "purpose": "System Log Control",
        "syntax": "ZLOG [DISPLAY|START|STOP|CLEAR] [filter]",
        "description": "Display or control the logging of system messages. Filter by message ID, severity, or program. Essential for monitoring and troubleshooting.",
        "output_fields": [
            "LOG STATUS: ACTIVE",
            "MSG COUNT: nnnnnnn",
            "LAST MSG: timestamp  ID: xxxxxxxx"
        ],
        "example": "ZLOG DISPLAY ERR",
        "category": "Logging",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "No messages match filter"
        }
    },
    "ZDTCP": {
        "purpose": "Display TCP/IP Connections",
        "syntax": "ZDTCP [DISPLAY|STATUS] [daemon|port]",
        "description": "Displays active TCP/IP sockets, connection states, and daemon bindings on z/TPF. Use with ZINET when diagnosing network hangs, stuck HTTP sessions, or WebBridge timeouts.",
        "output_fields": [
            "DAEMON: HTTP   PORT: 80    STATE: LISTEN",
            "CONN ID: nnnn  REMOTE: x.x.x.x:port  STATE: ESTABLISHED",
            "BYTES IN: nnnnnnnn  BYTES OUT: nnnnnnnn",
            "ACTIVE CONNECTIONS: nnn"
        ],
        "example": "ZDTCP DISPLAY HTTP",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "Daemon or port not found",
            "RC=8": "TCP stack not active"
        },
        "tos_note": "RAVEN execs can poll ZDTCP after ZINET DISPLAY to verify daemon health before automated restarts."
    },
    "ZACOR": {
        "purpose": "Alter core",
        "syntax": "ZACOR addr [data]",
        "description": "Modifies contents of main storage or specific core blocks.",
        "output_fields": [
            "ZACOR STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZACOR DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZALOC": {
        "purpose": "Allocate module",
        "syntax": "ZALOC [module]",
        "description": "Allocate or deallocate a module on a device for z/TPF use.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZALOC DISPLAY",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZAPL": {
        "purpose": "Application program load",
        "syntax": "ZAPL LOAD program",
        "description": "Load or delete an application program in the z/TPF system.",
        "output_fields": [
            "PROGRAM STATUS: LOADED/NOT LOADED",
            "CORE RESIDENCY: xxxxxxxx",
            "RC: 0"
        ],
        "example": "ZAPL",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZASER": {
        "purpose": "Assign serial number",
        "syntax": "ZASER vol_id",
        "description": "Assign or change a volume serial number for a disk.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZASER",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZATIM": {
        "purpose": "Alter time",
        "syntax": "ZATIM hh:mm:ss",
        "description": "Changes the z/TPF system time or date.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZATIM",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZAWEB": {
        "purpose": "Alter WebBridge",
        "syntax": "ZAWEB command",
        "description": "Control WebBridge subsystem processing.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZAWEB",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZAWFS": {
        "purpose": "Alter WebSphere MQ file system",
        "syntax": "ZAWFS command",
        "description": "Control MQSeries configurations.",
        "output_fields": [
            "QUEUE/CHANNEL STATUS: RUNNING",
            "DEPTH: nnn",
            "RC: 0"
        ],
        "example": "ZAWFS",
        "category": "Messaging",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZBDTA": {
        "purpose": "Background data",
        "syntax": "ZBDTA display",
        "description": "Display or alter background data capture settings.",
        "output_fields": [
            "ZBDTA STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZBDTA",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZBKG": {
        "purpose": "Background processor",
        "syntax": "ZBKG status",
        "description": "Start or stop background processing tasks or display their status.",
        "output_fields": [
            "ZBKG STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZBKG",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZBROW": {
        "purpose": "Browse files",
        "syntax": "ZBROW file",
        "description": "Browse system logs or disk records.",
        "output_fields": [
            "ZBROW STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZBROW",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZBUFS": {
        "purpose": "Buffer statistics",
        "syntax": "ZBUFS DISPLAY",
        "description": "Display statistics for VFA buffers and I/O operations.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZBUFS",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCAPT": {
        "purpose": "Capture data",
        "syntax": "ZCAPT start",
        "description": "Start or stop data capture for debugging or auditing.",
        "output_fields": [
            "ZCAPT COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZCAPT",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCDSP": {
        "purpose": "Core display",
        "syntax": "ZCDSP addr",
        "description": "Displays core memory contents or control blocks on the console.",
        "output_fields": [
            "ZCDSP COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZCDSP",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCIPC": {
        "purpose": "IPC control",
        "syntax": "ZCIPC display",
        "description": "Display Interprocess Communication (IPC) queues, semaphores, or shared memory.",
        "output_fields": [
            "ZCIPC STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZCIPC",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCOMP": {
        "purpose": "Compress data",
        "syntax": "ZCOMP status",
        "description": "Manage data compression dictionary and statistics.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZCOMP",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCONN": {
        "purpose": "Connection control",
        "syntax": "ZCONN display",
        "description": "Manage and display network connections or MQ channels.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZCONN",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCPRF": {
        "purpose": "C language profiling",
        "syntax": "ZCPRF start",
        "description": "Manage C/C++ program profiling.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZCPRF",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCTKA": {
        "purpose": "Control tape allocation",
        "syntax": "ZCTKA display",
        "description": "Alter or display tape allocation settings.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZCTKA",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZD0DB": {
        "purpose": "Database operator command",
        "syntax": "ZD0DB start",
        "description": "Start or stop z/TPF database capture and monitoring.",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZD0DB",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDBUG": {
        "purpose": "Debug console",
        "syntax": "ZDBUG term",
        "description": "Start an interactive trace and debug session for a specific terminal or ECB.",
        "output_fields": [
            "ZDBUG COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDBUG",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDDAT": {
        "purpose": "Display data",
        "syntax": "ZDDAT addr",
        "description": "Display records from a direct access storage device (DASD).",
        "output_fields": [
            "ZDDAT STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZDDAT",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDFL": {
        "purpose": "Display file logs",
        "syntax": "ZDFL view",
        "description": "Display online data file logs.",
        "output_fields": [
            "LOG STATUS: ACTIVE",
            "MESSAGE COUNT: nnnnn",
            "RC: 0"
        ],
        "example": "ZDFL",
        "category": "Logging",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDIR": {
        "purpose": "Display directory",
        "syntax": "ZDIR path",
        "description": "Display the contents of a directory in the hierarchical file system.",
        "output_fields": [
            "ZDIR STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZDIR",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDSK": {
        "purpose": "Disk control",
        "syntax": "ZDSK status",
        "description": "Display or alter disk device status and properties.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZDSK",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZERR": {
        "purpose": "Error log",
        "syntax": "ZERR display",
        "description": "Display hardware and software error logs and statistics.",
        "output_fields": [
            "LOG STATUS: ACTIVE",
            "MESSAGE COUNT: nnnnn",
            "RC: 0"
        ],
        "example": "ZERR",
        "category": "Logging",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZEVNT": {
        "purpose": "Event control",
        "syntax": "ZEVNT status",
        "description": "Manage system event monitoring and tracing.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZEVNT",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZFCAT": {
        "purpose": "File catalog",
        "syntax": "ZFCAT display",
        "description": "Display file catalog entries.",
        "output_fields": [
            "ZFCAT STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZFCAT",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZFILE": {
        "purpose": "File system control",
        "syntax": "ZFILE status",
        "description": "Manage z/TPF collection support file systems, mount directories, and display file status.",
        "output_fields": [
            "ZFILE STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZFILE",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZFSYS": {
        "purpose": "File system status",
        "syntax": "ZFSYS display",
        "description": "Display mounted z/TPF file systems and their usage.",
        "output_fields": [
            "ZFSYS STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZFSYS",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZFCRZ": {
        "purpose": "Format core zero",
        "syntax": "ZFCRZ",
        "description": "Format the CRZ area of main storage.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZFCRZ",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZGDCL": {
        "purpose": "Global data class",
        "syntax": "ZGDCL display",
        "description": "Manage global data classes and structures.",
        "output_fields": [
            "ZGDCL STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZGDCL",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZGLBL": {
        "purpose": "Global control",
        "syntax": "ZGLBL display",
        "description": "Display or alter global records or directories.",
        "output_fields": [
            "ZGLBL STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZGLBL",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZINFO": {
        "purpose": "System information",
        "syntax": "ZINFO ALL",
        "description": "Display general system status and configuration.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZINFO",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZISDN": {
        "purpose": "ISDN control",
        "syntax": "ZISDN status",
        "description": "Display or manage ISDN connections.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZISDN",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZJCL": {
        "purpose": "Job control",
        "syntax": "ZJCL status",
        "description": "Start or stop background JCL jobs.",
        "output_fields": [
            "ZJCL STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZJCL",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZKEY": {
        "purpose": "Keystore control",
        "syntax": "ZKEY display",
        "description": "Manage symmetric and asymmetric encryption keys.",
        "output_fields": [
            "KEYSTORE/PROFILE STATUS: ACTIVE",
            "RC: 0"
        ],
        "example": "ZKEY",
        "category": "Security",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZLOAD": {
        "purpose": "Load records",
        "syntax": "ZLOAD tape",
        "description": "Load fixed file records from tape to disk.",
        "output_fields": [
            "ZLOAD STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZLOAD",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZLSA": {
        "purpose": "Link status",
        "syntax": "ZLSA link_id",
        "description": "Display status and statistics for SNA or IP communication links.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZLSA",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMAIL": {
        "purpose": "Mail system",
        "syntax": "ZMAIL queue",
        "description": "Send messages or check mail queues in z/TPF.",
        "output_fields": [
            "ZMAIL STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZMAIL",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMAP": {
        "purpose": "Memory map",
        "syntax": "ZMAP addr",
        "description": "Display memory mapping information for programs or data.",
        "output_fields": [
            "ZMAP COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZMAP",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMEAS": {
        "purpose": "Measurement control",
        "syntax": "ZMEAS START",
        "description": "Start or stop performance measurement data collection.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZMEAS",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMOD": {
        "purpose": "Modify module",
        "syntax": "ZMOD module",
        "description": "Modify specific modules in the system.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZMOD",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMSG": {
        "purpose": "Message control",
        "syntax": "ZMSG route",
        "description": "Route or suppress specific system messages.",
        "output_fields": [
            "ZMSG STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZMSG",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMTA": {
        "purpose": "Message transfer agent",
        "syntax": "ZMTA status",
        "description": "Control MTA processing for mail routing.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZMTA",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZNET": {
        "purpose": "Network control",
        "syntax": "ZNET display",
        "description": "Display or alter network configurations, routes, and interfaces.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZNET",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZNKEY": {
        "purpose": "Encryption keys",
        "syntax": "ZNKEY list",
        "description": "Manage secure encryption keys in the z/TPF keystore.",
        "output_fields": [
            "KEYSTORE/PROFILE STATUS: ACTIVE",
            "RC: 0"
        ],
        "example": "ZNKEY",
        "category": "Security",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZNSDM": {
        "purpose": "Name server",
        "syntax": "ZNSDM display",
        "description": "Manage domain name server (DNS) settings.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZNSDM",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZONLN": {
        "purpose": "Online control",
        "syntax": "ZONLN module",
        "description": "Bring modules or devices online.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZONLN",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZOPTS": {
        "purpose": "System options",
        "syntax": "ZOPTS display",
        "description": "Display or change global system options and flags.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZOPTS",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZOSRV": {
        "purpose": "TPF Operations Server (TOS) Control",
        "syntax": "ZOSRV [DISPLAY|START|STOP|STATUS] [server_name]",
        "description": "Manages TPF Operations Server (TOS) connections used for REXX/RAVEN automation, scheduled jobs, and operational scripts. DISPLAY shows active TOS sessions; START/STOP control automation connectivity to z/TPF.",
        "output_fields": [
            "TOS SERVER: TOS1     STATUS: CONNECTED",
            "RAVEN EXECS ACTIVE: nnn",
            "LAST HEARTBEAT: timestamp",
            "PENDING JOBS: nnn"
        ],
        "example": "ZOSRV DISPLAY",
        "category": "Operations",
        "rc_codes": {
            "RC=0": "Success",
            "RC=4": "TOS server not configured",
            "RC=8": "Connection failed",
            "RC=12": "RAVEN subsystem unavailable"
        },
        "tos_note": "Primary command for TOS automation health checks before running REXX RAVEN execs."
    },
    "ZPAGE": {
        "purpose": "Terminal paging",
        "syntax": "ZPAGE [F|B]",
        "description": "Terminal paging operator command. Used to display and scroll through multi-page console output. Options: F (forward), B (backward).",
        "output_fields": [
            "ZPAGE STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZPAGE DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZPATH": {
        "purpose": "Path control",
        "syntax": "ZPATH display",
        "description": "Display or alter I/O paths to devices.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZPATH",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZPCTL": {
        "purpose": "Process control",
        "syntax": "ZPCTL ps",
        "description": "Manage UNIX-like processes in the z/TPF system.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZPCTL",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZPNR": {
        "purpose": "PNR control",
        "syntax": "ZPNR display",
        "description": "Display Passenger Name Record (PNR) details or metrics (application-specific).",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZPNR",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZPWB": {
        "purpose": "Password control",
        "syntax": "ZPWB user",
        "description": "Manage user passwords and security profiles.",
        "output_fields": [
            "KEYSTORE/PROFILE STATUS: ACTIVE",
            "RC: 0"
        ],
        "example": "ZPWB",
        "category": "Security",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZRCVA": {
        "purpose": "Recovery control",
        "syntax": "ZRCVA display",
        "description": "Manage system recovery parameters and restart options.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZRCVA",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZREXX": {
        "purpose": "REXX execution",
        "syntax": "ZREXX exec_name",
        "description": "Start a REXX exec or display active REXX environments.",
        "output_fields": [
            "PROGRAM STATUS: LOADED/NOT LOADED",
            "CORE RESIDENCY: xxxxxxxx",
            "RC: 0"
        ],
        "example": "ZREXX",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        },
        "tos_note": "Use in TOS/RAVEN automation: check RC after each command; pair with ZSTAT or ZLOG for operational monitoring."
    },
    "ZROUT": {
        "purpose": "Routing control",
        "syntax": "ZROUT display",
        "description": "Display or change message routing tables.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZROUT",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZRSVS": {
        "purpose": "Reserve storage",
        "syntax": "ZRSVS status",
        "description": "Manage reserve storage for critical system functions.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZRSVS",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSDTA": {
        "purpose": "System data",
        "syntax": "ZSDTA display",
        "description": "Display or alter system data constants.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZSDTA",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSONA": {
        "purpose": "SONA control",
        "syntax": "ZSONA status",
        "description": "Manage SNA over Native IP configurations.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZSONA",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSSBP": {
        "purpose": "Subsystem routing",
        "syntax": "ZSSBP display",
        "description": "Switch or display subsystem routing status and pool usage.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZSSBP",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSTOP": {
        "purpose": "System stop",
        "syntax": "ZSTOP subsystem",
        "description": "Stop a specific subsystem or the entire z/TPF system gracefully.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZSTOP",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSTRC": {
        "purpose": "System trace",
        "syntax": "ZSTRC start",
        "description": "Start or stop system-level tracing.",
        "output_fields": [
            "ZSTRC COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZSTRC",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTAPE": {
        "purpose": "Tape control",
        "syntax": "ZTAPE display",
        "description": "Display or manage tape drives, labels, and mounts.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZTAPE",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTCP": {
        "purpose": "TCP/IP control",
        "syntax": "ZTCP status",
        "description": "Display or modify TCP/IP stack configuration.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZTCP",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTMON": {
        "purpose": "Tape monitor",
        "syntax": "ZTMON display",
        "description": "Display tape drive status and volume mounts.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZTMON",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTSTR": {
        "purpose": "Test structure",
        "syntax": "ZTSTR create",
        "description": "Create or modify test data structures.",
        "output_fields": [
            "ZTSTR COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZTSTR",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZVAL": {
        "purpose": "Validate",
        "syntax": "ZVAL pool",
        "description": "Validate file pool structures or formats.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZVAL",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZVFA": {
        "purpose": "Virtual File Access",
        "syntax": "ZVFA display",
        "description": "Display or alter VFA cache settings and hit ratios.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZVFA",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZVOL": {
        "purpose": "Volume control",
        "syntax": "ZVOL label",
        "description": "Display volume labels and status.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZVOL",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZXCF": {
        "purpose": "Coupling facility",
        "syntax": "ZXCF status",
        "description": "Manage XCF communication and coupling facility structures.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZXCF",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZADCD": {
        "purpose": "Add data collection definition",
        "syntax": "ZADCD [DISPLAY|STATUS]",
        "description": "Defines a data collection scenario.",
        "output_fields": [
            "ZADCD STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZADCD DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZADD": {
        "purpose": "Add",
        "syntax": "ZADD [DISPLAY|STATUS]",
        "description": "Add records, files, or definitions.",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZADD DISPLAY",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZALDC": {
        "purpose": "Allocate logic",
        "syntax": "ZALDC [DISPLAY|STATUS]",
        "description": "Allocate devices or logical units for z/TPF.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZALDC DISPLAY",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZALTR": {
        "purpose": "Alter subsystem",
        "syntax": "ZALTR [ALTER|STATUS]",
        "description": "Alter subsystem or resource parameters.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZALTR DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZAUD": {
        "purpose": "Audit",
        "syntax": "ZAUD [DISPLAY|STATUS]",
        "description": "Display audit trail and compliance logs.",
        "output_fields": [
            "LOG STATUS: ACTIVE",
            "MESSAGE COUNT: nnnnn",
            "RC: 0"
        ],
        "example": "ZAUD DISPLAY",
        "category": "Logging",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZBACK": {
        "purpose": "Backup control",
        "syntax": "ZBACK [DISPLAY|STATUS]",
        "description": "Manage backup and recovery operations.",
        "output_fields": [
            "ZBACK STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZBACK DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZBAL": {
        "purpose": "BAL loader",
        "syntax": "ZBAL [DISPLAY|STATUS]",
        "description": "Display or control BAL program load.",
        "output_fields": [
            "PROGRAM STATUS: LOADED/NOT LOADED",
            "CORE RESIDENCY: xxxxxxxx",
            "RC: 0"
        ],
        "example": "ZBAL DISPLAY",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCHK": {
        "purpose": "Check",
        "syntax": "ZCHK [DISPLAY|STATUS]",
        "description": "Validate system or file integrity.",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZCHK DISPLAY",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCNFG": {
        "purpose": "Configuration",
        "syntax": "ZCNFG [DISPLAY|STATUS]",
        "description": "Display or alter system configuration.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZCNFG DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCOPY": {
        "purpose": "Copy",
        "syntax": "ZCOPY [DISPLAY|STATUS]",
        "description": "Copy records or files between pools.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZCOPY DISPLAY",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCRYPT": {
        "purpose": "Cryptography",
        "syntax": "ZCRYPT [DISPLAY|STATUS]",
        "description": "Manage encryption subsystem settings.",
        "output_fields": [
            "KEYSTORE/PROFILE STATUS: ACTIVE",
            "RC: 0"
        ],
        "example": "ZCRYPT DISPLAY",
        "category": "Security",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZCSECT": {
        "purpose": "CSECT control",
        "syntax": "ZCSECT [DISPLAY|STATUS]",
        "description": "Display loaded CSECTs and entry points.",
        "output_fields": [
            "PROGRAM STATUS: LOADED/NOT LOADED",
            "CORE RESIDENCY: xxxxxxxx",
            "RC: 0"
        ],
        "example": "ZCSECT DISPLAY",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDCPD": {
        "purpose": "Display CP definitions",
        "syntax": "ZDCPD [DISPLAY|STATUS]",
        "description": "Shows Central Processor configuration.",
        "output_fields": [
            "ZDCPD COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDCPD DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDDTA": {
        "purpose": "Display data capture",
        "syntax": "ZDDTA [DISPLAY|STATUS]",
        "description": "Shows active data capture scenarios and buffers.",
        "output_fields": [
            "ZDDTA COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDDTA DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDEL": {
        "purpose": "Delete",
        "syntax": "ZDEL [DISPLAY|STATUS]",
        "description": "Delete records, files, or definitions.",
        "output_fields": [
            "ZDEL COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDEL DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDHIS": {
        "purpose": "Display history",
        "syntax": "ZDHIS [DISPLAY|STATUS]",
        "description": "Shows historical system events, tape mounts, or operator actions.",
        "output_fields": [
            "ZDHIS COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDHIS DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDISP": {
        "purpose": "Display control",
        "syntax": "ZDISP [DISPLAY|STATUS]",
        "description": "Generic display subsystem operator command.",
        "output_fields": [
            "ZDISP COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDISP DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDLI": {
        "purpose": "DL/I control",
        "syntax": "ZDLI [DISPLAY|STATUS]",
        "description": "Manage IMS/DLI database interfaces on z/TPF.",
        "output_fields": [
            "ZDLI COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDLI DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDMSG": {
        "purpose": "Display message",
        "syntax": "ZDMSG [DISPLAY|STATUS]",
        "description": "Shows routing parameters for specific message numbers.",
        "output_fields": [
            "ZDMSG COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDMSG DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDPVL": {
        "purpose": "Display pool volumes",
        "syntax": "ZDPVL [DISPLAY|STATUS]",
        "description": "Shows disk pool volume attributes and status.",
        "output_fields": [
            "ZDPVL COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDPVL DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDSCT": {
        "purpose": "Display sector",
        "syntax": "ZDSCT [DISPLAY|STATUS]",
        "description": "Displays hardware sector formats or DASD usage.",
        "output_fields": [
            "ZDSCT COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDSCT DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDTIM": {
        "purpose": "Display time",
        "syntax": "ZDTIM [DISPLAY|STATUS]",
        "description": "Displays current system clock and time-of-day settings.",
        "output_fields": [
            "ZDTIM COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDTIM DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDTRP": {
        "purpose": "Display traps",
        "syntax": "ZDTRP [DISPLAY|STATUS]",
        "description": "Shows active diagnostic traps (complement to ZTRAP).",
        "output_fields": [
            "ZDTRP COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDTRP DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZDUIN": {
        "purpose": "Display UINs",
        "syntax": "ZDUIN [DISPLAY|STATUS]",
        "description": "Displays Unique Identifier Numbers and allocation.",
        "output_fields": [
            "ZDUIN COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZDUIN DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZENTRY": {
        "purpose": "Entry control",
        "syntax": "ZENTRY [DISPLAY|STATUS]",
        "description": "Display transaction entry definitions.",
        "output_fields": [
            "PROGRAM STATUS: LOADED/NOT LOADED",
            "CORE RESIDENCY: xxxxxxxx",
            "RC: 0"
        ],
        "example": "ZENTRY DISPLAY",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZFIX": {
        "purpose": "Fix",
        "syntax": "ZFIX [DISPLAY|STATUS]",
        "description": "Repair file or index structures.",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZFIX DISPLAY",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZFTP": {
        "purpose": "FTP daemon",
        "syntax": "ZFTP [DISPLAY|STATUS]",
        "description": "Control FTP subsystem connections.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZFTP DISPLAY",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZHELP": {
        "purpose": "Help",
        "syntax": "ZHELP [DISPLAY|STATUS]",
        "description": "Display operator command help text.",
        "output_fields": [
            "ZHELP STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZHELP DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZHTTP": {
        "purpose": "HTTP daemon",
        "syntax": "ZHTTP [DISPLAY|STATUS]",
        "description": "Control HTTP subsystem on z/TPF.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZHTTP DISPLAY",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZINIT": {
        "purpose": "Initialize",
        "syntax": "ZINIT [DISPLAY|STATUS]",
        "description": "Initialize subsystem or device for processing.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZINIT DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZJB": {
        "purpose": "Job batch",
        "syntax": "ZJB [DISPLAY|STATUS]",
        "description": "Submit or display batch jobs.",
        "output_fields": [
            "ZJB STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZJB DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZJSON": {
        "purpose": "JSON processing",
        "syntax": "ZJSON [DISPLAY|STATUS]",
        "description": "Display JSON/WebBridge transform status.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZJSON DISPLAY",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZLDAP": {
        "purpose": "LDAP",
        "syntax": "ZLDAP [DISPLAY|STATUS]",
        "description": "Display directory service bindings.",
        "output_fields": [
            "ZLDAP STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZLDAP DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZLIC": {
        "purpose": "License",
        "syntax": "ZLIC [DISPLAY|STATUS]",
        "description": "Display license and entitlement information.",
        "output_fields": [
            "ZLIC STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZLIC DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZLIST": {
        "purpose": "List",
        "syntax": "ZLIST [DISPLAY|STATUS]",
        "description": "List catalog, directory, or queue contents.",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZLIST DISPLAY",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZLOADR": {
        "purpose": "Loader control",
        "syntax": "ZLOADR [DISPLAY|STATUS]",
        "description": "Extended program load utilities.",
        "output_fields": [
            "PROGRAM STATUS: LOADED/NOT LOADED",
            "CORE RESIDENCY: xxxxxxxx",
            "RC: 0"
        ],
        "example": "ZLOADR DISPLAY",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMIG": {
        "purpose": "Migration",
        "syntax": "ZMIG [DISPLAY|STATUS]",
        "description": "Control data migration utilities.",
        "output_fields": [
            "ZMIG STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZMIG DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMON": {
        "purpose": "Monitor",
        "syntax": "ZMON [DISPLAY|STATUS]",
        "description": "Start continuous monitoring of entry or resource.",
        "output_fields": [
            "PROGRAM STATUS: LOADED/NOT LOADED",
            "CORE RESIDENCY: xxxxxxxx",
            "RC: 0"
        ],
        "example": "ZMON DISPLAY",
        "category": "Program",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZMOVE": {
        "purpose": "Move",
        "syntax": "ZMOVE [DISPLAY|STATUS]",
        "description": "Move volumes or datasets.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZMOVE DISPLAY",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZPARM": {
        "purpose": "Display parameters",
        "syntax": "ZPARM [DISPLAY|STATUS]",
        "description": "Show system parameter settings.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZPARM DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZPING": {
        "purpose": "Ping TCP/IP node",
        "syntax": "ZPING [DISPLAY|STATUS]",
        "description": "Verify network connectivity from z/TPF.",
        "output_fields": [
            "LINK/DAEMON STATUS: ACTIVE",
            "CONNECTIONS: nnn",
            "RC: 0"
        ],
        "example": "ZPING DISPLAY",
        "category": "Network",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZPRNT": {
        "purpose": "Print control",
        "syntax": "ZPRNT [DISPLAY|STATUS]",
        "description": "Route output to printer or spool.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZPRNT DISPLAY",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZQUE": {
        "purpose": "Queue control",
        "syntax": "ZQUE [DISPLAY|STATUS]",
        "description": "Display or alter message/transaction queues.",
        "output_fields": [
            "ZQUE STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZQUE DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZREBLD": {
        "purpose": "Rebuild",
        "syntax": "ZREBLD [DISPLAY|STATUS]",
        "description": "Rebuild indexes or file structures.",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZREBLD DISPLAY",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZREFR": {
        "purpose": "Refresh",
        "syntax": "ZREFR [DISPLAY|STATUS]",
        "description": "Refresh cached definitions or tables.",
        "output_fields": [
            "ZREFR STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZREFR DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZREST": {
        "purpose": "Restart control",
        "syntax": "ZREST [DISPLAY|STATUS]",
        "description": "Manage warm/cold restart options.",
        "output_fields": [
            "ZREST STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZREST DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSECU": {
        "purpose": "Security control",
        "syntax": "ZSECU [DISPLAY|STATUS]",
        "description": "Display security subsystem status.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZSECU DISPLAY",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSEG": {
        "purpose": "Segment control",
        "syntax": "ZSEG [DISPLAY|STATUS]",
        "description": "Display program segment status.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZSEG DISPLAY",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSHUT": {
        "purpose": "Shutdown",
        "syntax": "ZSHUT [DISPLAY|STATUS]",
        "description": "Gracefully shut down subsystem or service.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZSHUT DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSMTP": {
        "purpose": "SMTP/mail daemon",
        "syntax": "ZSMTP [DISPLAY|STATUS]",
        "description": "Control mail transfer agent.",
        "output_fields": [
            "QUEUE/CHANNEL STATUS: RUNNING",
            "DEPTH: nnn",
            "RC: 0"
        ],
        "example": "ZSMTP DISPLAY",
        "category": "Messaging",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSOAP": {
        "purpose": "Web services",
        "syntax": "ZSOAP [DISPLAY|STATUS]",
        "description": "Control SOAP/REST gateway (WebBridge related).",
        "output_fields": [
            "ZSOAP STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZSOAP DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSORT": {
        "purpose": "Sort utility",
        "syntax": "ZSORT [DISPLAY|STATUS]",
        "description": "Control z/TPF sort processing.",
        "output_fields": [
            "ZSORT STATUS: COMPLETE",
            "RC: 0"
        ],
        "example": "ZSORT DISPLAY",
        "category": "General",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSPOL": {
        "purpose": "Spool control",
        "syntax": "ZSPOL [DISPLAY|STATUS]",
        "description": "Manage output spooling queues.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZSPOL DISPLAY",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSSL": {
        "purpose": "SSL/TLS",
        "syntax": "ZSSL [DISPLAY|STATUS]",
        "description": "Display secure socket layer configuration.",
        "output_fields": [
            "KEYSTORE/PROFILE STATUS: ACTIVE",
            "RC: 0"
        ],
        "example": "ZSSL DISPLAY",
        "category": "Security",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZSYSM": {
        "purpose": "System messages",
        "syntax": "ZSYSM [DISPLAY|STATUS]",
        "description": "Toggle and configure system message processing.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZSYSM DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTERM": {
        "purpose": "Terminal control",
        "syntax": "ZTERM [DISPLAY|STATUS]",
        "description": "Display or alter terminal session status.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZTERM DISPLAY",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTIMA": {
        "purpose": "Time alteration",
        "syntax": "ZTIMA [DISPLAY|STATUS]",
        "description": "Manage system timeout thresholds and timers.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZTIMA DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTRAC": {
        "purpose": "System trace",
        "syntax": "ZTRAC [DISPLAY|STATUS]",
        "description": "Start or stop specific traces for programs or subsystems.",
        "output_fields": [
            "ZTRAC COMPLETED \u2014 RC=0",
            "DIAGNOSTIC DATA: displayed on console",
            "RC: 0"
        ],
        "example": "ZTRAC DISPLAY",
        "category": "Diagnostic",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZTRBL": {
        "purpose": "Troubleshoot",
        "syntax": "ZTRBL [DISPLAY|STATUS]",
        "description": "Diagnose system events and error conditions.",
        "output_fields": [
            "LOG STATUS: ACTIVE",
            "MESSAGE COUNT: nnnnn",
            "RC: 0"
        ],
        "example": "ZTRBL DISPLAY",
        "category": "Logging",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZUNLD": {
        "purpose": "Unload",
        "syntax": "ZUNLD [DISPLAY|STATUS]",
        "description": "Unload programs or modules from core.",
        "output_fields": [
            "DEVICE/POOL STATUS: ACTIVE",
            "BLOCKS/CAPACITY: nnnnn used / nnnnn free",
            "RC: 0"
        ],
        "example": "ZUNLD DISPLAY",
        "category": "Storage",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZUSER": {
        "purpose": "User control",
        "syntax": "ZUSER [DISPLAY|STATUS]",
        "description": "Display operator/user profiles and authority.",
        "output_fields": [
            "DB/FILE STATUS: ACTIVE",
            "RECORDS/INDEX: valid",
            "RC: 0"
        ],
        "example": "ZUSER DISPLAY",
        "category": "Database",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZUTIL": {
        "purpose": "Utilities control",
        "syntax": "ZUTIL [DISPLAY|STATUS]",
        "description": "Invoke z/TPF system utilities.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZUTIL DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZVER": {
        "purpose": "Version display",
        "syntax": "ZVER [DISPLAY|STATUS]",
        "description": "Show z/TPF and subsystem version levels.",
        "output_fields": [
            "SYSTEM STATUS: ACTIVE",
            "SUBSYSTEM: NORMAL",
            "RC: 0"
        ],
        "example": "ZVER DISPLAY",
        "category": "System Status",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    },
    "ZXML": {
        "purpose": "XML processing",
        "syntax": "ZXML [DISPLAY|STATUS]",
        "description": "Display XML parser/transform status.",
        "output_fields": [
            "METRIC COLLECTION: ACTIVE",
            "CPU/IO RATES: nn.nn%",
            "RC: 0"
        ],
        "example": "ZXML DISPLAY",
        "category": "Performance",
        "rc_codes": {
            "RC=0": "Success \u2014 command completed",
            "RC=4": "Warning \u2014 resource not found or partial result",
            "RC=8": "Error \u2014 command failed or subsystem unavailable",
            "RC=12": "Severe error \u2014 operator intervention required"
        }
    }
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

    
    "system_error_codes": """
IBM z/TPF System Error Codes:
- RC=X'00': Success, no errors.
- RC=X'04': Resource not found (e.g., FINDA record not found).
- RC=X'08': System error / I/O error / Database index corrupt.
- RC=X'0C' (12): Storage failure (e.g., GETCC memory pool exhausted).
- RC=X'10' (16): Validation failure / Invalid parameters provided.
- CTL-X / SERR: System error dump triggered. Check ZDUMP.
""",

    "pnr_structure": """
PNR (Passenger Name Record) Structure for Airline Use:
A PNR is a complex hierarchical data structure stored in TPFDF.
- Core Data (LREC 01): Locator (8 chars), Creation Date, Agent ID.
- Passenger Name (LREC 02): Last name, First name, Title, frequent flyer ID.
- Flight Segment (LREC 03): Airline code, Flight number, Class, Origin, Destination, Date.
- SSR (Special Service Request): Meal types, Wheelchair requests.
- OSI (Other Service Information): VIP indicators.
- Fare/Pricing (LREC 05): Fare basis code, Ticket numbers, Pricing parameters.
""",

    "tpfdf_schema": """
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
""",

    "ce1cr0_offsets": """
CE1CR0 Input Data Area Offsets (Common Mapping):
CE1CR0 is a 4KB core block attached to ECB level D0 upon transaction entry.
- Offset 0-7: Primary Key / Locator (8 bytes, CHAR)
- Offset 8: Request Type / Action Code (1 byte, BIN) - X'00' Read, X'01' Update
- Offset 9-11: Flags and routing indicators
- Offset 12-15: Message Length (4 bytes, BIN)
- Offset 16-31: Session Token / Terminal ID
- Offset 32+: Payload Data (e.g., XML/JSON payload or structured BAL input)
""",

    "subsystem_knowledge": """
Subsystem Interactions with z/TPF:
- INET (Internet Daemon): Handles TCP/IP sockets. Dispatches an ECB for each incoming HTTP/FTP request.
- WebBridge: Translates REST/JSON calls from external web clients into traditional z/TPF ECB structures. Maps JSON to CE1CR0.
- MQ (WebSphere MQ): Asynchronous messaging. z/TPF acts as a queue manager via ZMQSC. Pulls messages off queues and dispatches ECBs.
- SNA (Systems Network Architecture): Legacy airline routing (ALC protocols). Handled by ZNET and ZSONA.
""",

    "tos_automation": """
TPF Operations Server (TOS) and REXX/RAVEN Automation for z/TPF

TOS provides off-host automation that issues z/TPF operator commands and monitors entries.
RAVEN is the REXX execution environment on TOS.

─── TOS AUTOMATION WORKFLOW ───────────────────────────────────────────────────
1. Verify TOS connectivity: ZOSRV DISPLAY
2. Check target entry loaded: ZPROG DISPLAY entry_name
3. Monitor system health: ZDSYS ALL, ZSTAT ALL
4. Run RAVEN exec: ZREXX exec_name (or schedule via TOS job)
5. On errors: ZDECB ecb_addr, ZDUMP ecb_addr FULL, ZLOG DISPLAY ERR

─── VAR / TDRV / TDR ARTIFACTS FOR TOS ────────────────────────────────────────
- VAR:  Documents all transaction variables (fixed-width columns)
- TDRV: Step-by-step test driver for validation and walkthrough
- TDR:  Transaction Design Record — purpose, I/O, exceptions, Z-Commands

STS Coder generates these artifacts from BAL assembly to support TOS test automation.

─── EXPECTED Z-COMMAND RESPONSES IN REXX ─────────────────────────────────────
After 'ZSTAT ALL' in RAVEN: RC=0 means success; non-zero triggers diagnostic path.
'ZPROG DISPLAY TR001' → LOADED or NOT LOADED in console output.
'ZOSRV DISPLAY' → CONNECTED when TOS can reach z/TPF.
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
    "tos": "tos_automation",
    "operations server": "tos_automation",
    "tpf operations": "tos_automation",
    "automation": "tos_automation",
    "variation": "var_file",
    "var file": "var_file",
    "zdtcp": "subsystem_knowledge",
    "tcp": "subsystem_knowledge",
    "zcmd": "overview",
    "z-command": "overview",
    "z command": "overview",
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
    "z_commands": {
    "ZACOR": "Alter core. Modifies contents of main storage or specific core blocks.",
    "ZADCD": "Add data collection definition. Defines a data collection scenario.",
    "ZADD": "Add. Add records, files, or definitions.",
    "ZALDC": "Allocate logic. Allocate devices or logical units for z/TPF.",
    "ZALOC": "Allocate module. Allocate or deallocate a module on a device for z/TPF use.",
    "ZALTR": "Alter subsystem. Alter subsystem or resource parameters.",
    "ZAPL": "Application program load. Load or delete an application program in the z/TPF system.",
    "ZASER": "Assign serial number. Assign or change a volume serial number for a disk.",
    "ZATIM": "Alter time. Changes the z/TPF system time or date.",
    "ZAUD": "Audit. Display audit trail and compliance logs.",
    "ZAWEB": "Alter WebBridge. Control WebBridge subsystem processing.",
    "ZAWFS": "Alter WebSphere MQ file system. Control MQSeries configurations.",
    "ZBACK": "Backup control. Manage backup and recovery operations.",
    "ZBAL": "BAL loader. Display or control BAL program load.",
    "ZBDTA": "Background data. Display or alter background data capture settings.",
    "ZBKG": "Background processor. Start or stop background processing tasks or display their status.",
    "ZBROW": "Browse files. Browse system logs or disk records.",
    "ZBUFS": "Buffer statistics. Display statistics for VFA buffers and I/O operations.",
    "ZCAPT": "Capture data. Start or stop data capture for debugging or auditing.",
    "ZCDSP": "Core display. Displays core memory contents or control blocks on the console.",
    "ZCHK": "Check. Validate system or file integrity.",
    "ZCIPC": "IPC control. Display Interprocess Communication (IPC) queues, semaphores, or shared memory.",
    "ZCNFG": "Configuration. Display or alter system configuration.",
    "ZCOMP": "Compress data. Manage data compression dictionary and statistics.",
    "ZCONN": "Connection control. Manage and display network connections or MQ channels.",
    "ZCOPY": "Copy. Copy records or files between pools.",
    "ZCPRF": "C language profiling. Manage C/C++ program profiling.",
    "ZCRYPT": "Cryptography. Manage encryption subsystem settings.",
    "ZCSECT": "CSECT control. Display loaded CSECTs and entry points.",
    "ZCTKA": "Control tape allocation. Alter or display tape allocation settings.",
    "ZD0DB": "Database operator command. Start or stop z/TPF database capture and monitoring.",
    "ZDBUG": "Debug console. Start an interactive trace and debug session for a specific terminal or ECB.",
    "ZDCPD": "Display CP definitions. Shows Central Processor configuration.",
    "ZDDAT": "Display data. Display records from a direct access storage device (DASD).",
    "ZDDTA": "Display data capture. Shows active data capture scenarios and buffers.",
    "ZDECB": "Display ECB Data Levels. Dumps ECB data levels (D0 through DF), registers, and specific core block contents for debugging. Essential for post-mortem analysis.",
    "ZDEL": "Delete. Delete records, files, or definitions.",
    "ZDFL": "Display file logs. Display online data file logs.",
    "ZDHIS": "Display history. Shows historical system events, tape mounts, or operator actions.",
    "ZDIR": "Display directory. Display the contents of a directory in the hierarchical file system.",
    "ZDISP": "Display control. Generic display subsystem operator command.",
    "ZDLI": "DL/I control. Manage IMS/DLI database interfaces on z/TPF.",
    "ZDMSG": "Display message. Shows routing parameters for specific message numbers.",
    "ZDPVL": "Display pool volumes. Shows disk pool volume attributes and status.",
    "ZDSCT": "Display sector. Displays hardware sector formats or DASD usage.",
    "ZDSK": "Disk control. Display or alter disk device status and properties.",
    "ZDSYS": "Display System Status. Displays comprehensive z/TPF system status including CPU utilization, MDB (Message Data Block) state, cross-processor communication metrics, and active subsystem states.",
    "ZDTCP": "Display TCP/IP Connections. Displays active TCP/IP sockets, connection states, and daemon bindings on z/TPF. Use with ZINET when diagnosing network hangs, stuck HTTP sessions, or WebBridge timeouts.",
    "ZDTIM": "Display time. Displays current system clock and time-of-day settings.",
    "ZDTRP": "Display traps. Shows active diagnostic traps (complement to ZTRAP).",
    "ZDUIN": "Display UINs. Displays Unique Identifier Numbers and allocation.",
    "ZDUMP": "Memory Dump. Captures the contents of memory for a specific ECB or system area. Output includes all data levels, registers, PSW, and program chain for post-mortem analysis.",
    "ZECB": "ECB Control and Display. Display or alter the contents of active Entry Control Blocks. Can start/stop tracing on specific ECBs for debugging. Shows ECB state, program chain, and data levels.",
    "ZENTRY": "Entry control. Display transaction entry definitions.",
    "ZERR": "Error log. Display hardware and software error logs and statistics.",
    "ZEVNT": "Event control. Manage system event monitoring and tracing.",
    "ZFCAT": "File catalog. Display file catalog entries.",
    "ZFCRZ": "Format core zero. Format the CRZ area of main storage.",
    "ZFILE": "File system control. Manage z/TPF collection support file systems, mount directories, and display file status.",
    "ZFIX": "Fix. Repair file or index structures.",
    "ZFSYS": "File system status. Display mounted z/TPF file systems and their usage.",
    "ZFTP": "FTP daemon. Control FTP subsystem connections.",
    "ZGDCL": "Global data class. Manage global data classes and structures.",
    "ZGLBL": "Global control. Display or alter global records or directories.",
    "ZHELP": "Help. Display operator command help text.",
    "ZHTTP": "HTTP daemon. Control HTTP subsystem on z/TPF.",
    "ZINET": "Internet / TCP-IP Daemon Control. Manages z/TPF TCP/IP sockets, starts/stops daemons (HTTP, FTP, SMTP), and displays active network connections and daemon status.",
    "ZINFO": "System information. Display general system status and configuration.",
    "ZINIT": "Initialize. Initialize subsystem or device for processing.",
    "ZISDN": "ISDN control. Display or manage ISDN connections.",
    "ZJB": "Job batch. Submit or display batch jobs.",
    "ZJCL": "Job control. Start or stop background JCL jobs.",
    "ZJSON": "JSON processing. Display JSON/WebBridge transform status.",
    "ZKEY": "Keystore control. Manage symmetric and asymmetric encryption keys.",
    "ZLDAP": "LDAP. Display directory service bindings.",
    "ZLIC": "License. Display license and entitlement information.",
    "ZLIST": "List. List catalog, directory, or queue contents.",
    "ZLOAD": "Load records. Load fixed file records from tape to disk.",
    "ZLOADR": "Loader control. Extended program load utilities.",
    "ZLOG": "System Log Control. Display or control the logging of system messages. Filter by message ID, severity, or program. Essential for monitoring and troubleshooting.",
    "ZLSA": "Link status. Display status and statistics for SNA or IP communication links.",
    "ZMAIL": "Mail system. Send messages or check mail queues in z/TPF.",
    "ZMAP": "Memory map. Display memory mapping information for programs or data.",
    "ZMEAS": "Measurement control. Start or stop performance measurement data collection.",
    "ZMIG": "Migration. Control data migration utilities.",
    "ZMOD": "Modify module. Modify specific modules in the system.",
    "ZMON": "Monitor. Start continuous monitoring of entry or resource.",
    "ZMOVE": "Move. Move volumes or datasets.",
    "ZMQSC": "WebSphere MQ Control. Manage WebSphere MQ queue managers, queues, and channels on z/TPF. Display message depth, channel status, and connection counts.",
    "ZMSG": "Message control. Route or suppress specific system messages.",
    "ZMTA": "Message transfer agent. Control MTA processing for mail routing.",
    "ZNET": "Network control. Display or alter network configurations, routes, and interfaces.",
    "ZNKEY": "Encryption keys. Manage secure encryption keys in the z/TPF keystore.",
    "ZNSDM": "Name server. Manage domain name server (DNS) settings.",
    "ZONLN": "Online control. Bring modules or devices online.",
    "ZOPTS": "System options. Display or change global system options and flags.",
    "ZOSRV": "TPF Operations Server (TOS) Control. Manages TPF Operations Server (TOS) connections used for REXX/RAVEN automation, scheduled jobs, and operational scripts. DISPLAY shows active TOS sessions; START/STOP control automation connectivity to z/TPF.",
    "ZPAGE": "Terminal paging. Terminal paging operator command. Used to display and scroll through multi-page console output. Options: F (forward), B (backward).",
    "ZPARM": "Display parameters. Show system parameter settings.",
    "ZPATH": "Path control. Display or alter I/O paths to devices.",
    "ZPCTL": "Process control. Manage UNIX-like processes in the z/TPF system.",
    "ZPING": "Ping TCP/IP node. Verify network connectivity from z/TPF.",
    "ZPNR": "PNR control. Display Passenger Name Record (PNR) details or metrics (application-specific).",
    "ZPOOL": "Storage Pool Status. Display the status of z/TPF core storage pools including available blocks, peak usage, and allocation rates. Critical for detecting memory leaks (GETCC without RELCC).",
    "ZPRNT": "Print control. Route output to printer or spool.",
    "ZPROG": "Program Load/Status Control. Display program attributes, load status, and core residency. Load or delete application programs dynamically without system IPL.",
    "ZPWB": "Password control. Manage user passwords and security profiles.",
    "ZQUE": "Queue control. Display or alter message/transaction queues.",
    "ZRCVA": "Recovery control. Manage system recovery parameters and restart options.",
    "ZREBLD": "Rebuild. Rebuild indexes or file structures.",
    "ZREFR": "Refresh. Refresh cached definitions or tables.",
    "ZREST": "Restart control. Manage warm/cold restart options.",
    "ZREXX": "REXX execution. Start a REXX exec or display active REXX environments.",
    "ZROUT": "Routing control. Display or change message routing tables.",
    "ZRSVS": "Reserve storage. Manage reserve storage for critical system functions.",
    "ZSDTA": "System data. Display or alter system data constants.",
    "ZSECU": "Security control. Display security subsystem status.",
    "ZSEG": "Segment control. Display program segment status.",
    "ZSHUT": "Shutdown. Gracefully shut down subsystem or service.",
    "ZSMTP": "SMTP/mail daemon. Control mail transfer agent.",
    "ZSOAP": "Web services. Control SOAP/REST gateway (WebBridge related).",
    "ZSONA": "SONA control. Manage SNA over Native IP configurations.",
    "ZSORT": "Sort utility. Control z/TPF sort processing.",
    "ZSPOL": "Spool control. Manage output spooling queues.",
    "ZSSBP": "Subsystem routing. Switch or display subsystem routing status and pool usage.",
    "ZSSL": "SSL/TLS. Display secure socket layer configuration.",
    "ZSTAT": "System Statistics. Displays real-time z/TPF system performance metrics including ECB utilization, core block levels, I/O rates, and CPU consumption per processor.",
    "ZSTOP": "System stop. Stop a specific subsystem or the entire z/TPF system gracefully.",
    "ZSTRC": "System trace. Start or stop system-level tracing.",
    "ZSYSM": "System messages. Toggle and configure system message processing.",
    "ZTAPE": "Tape control. Display or manage tape drives, labels, and mounts.",
    "ZTCP": "TCP/IP control. Display or modify TCP/IP stack configuration.",
    "ZTERM": "Terminal control. Display or alter terminal session status.",
    "ZTIMA": "Time alteration. Manage system timeout thresholds and timers.",
    "ZTMON": "Tape monitor. Display tape drive status and volume mounts.",
    "ZTPFDF": "TPFDF Database Management. Create, display, and manage TPFDF (TPF Database Facility) databases and structures. Manage table definitions, indexes, and data organization.",
    "ZTRAC": "System trace. Start or stop specific traces for programs or subsystems.",
    "ZTRAP": "Diagnostic Software Trap. Set, display, or delete software traps to intercept program execution for debugging. When an ECB hits the trap address, execution is suspended and a dump is taken.",
    "ZTRBL": "Troubleshoot. Diagnose system events and error conditions.",
    "ZTSTR": "Test structure. Create or modify test data structures.",
    "ZUNLD": "Unload. Unload programs or modules from core.",
    "ZUSER": "User control. Display operator/user profiles and authority.",
    "ZUTIL": "Utilities control. Invoke z/TPF system utilities.",
    "ZVAL": "Validate. Validate file pool structures or formats.",
    "ZVER": "Version display. Show z/TPF and subsystem version levels.",
    "ZVFA": "Virtual File Access. Display or alter VFA cache settings and hit ratios.",
    "ZVOL": "Volume control. Display volume labels and status.",
    "ZXCF": "Coupling facility. Manage XCF communication and coupling facility structures.",
    "ZXML": "XML processing. Display XML parser/transform status."
},
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


# ─── Z-COMMAND FORMATTING HELPERS ───

def parse_zcmd_verb(command: str) -> str:
    """Extract base Z-command verb from operator input."""
    if not command or not command.strip():
        return ""
    return command.strip().split()[0].upper()


def format_zcmd_explanation(command: str, detail: dict | None = None) -> str:
    """Build a structured Z-command explanation from ZCMD_RESPONSES."""
    base_cmd = parse_zcmd_verb(command) or (command.strip().upper() if command else "")
    if detail is None:
        detail = ZCMD_RESPONSES.get(base_cmd)
    if not detail:
        kb = KNOWLEDGE.get("z_commands", {}).get(base_cmd, "")
        if kb:
            return (
                f"**Command:** {base_cmd}\n"
                f"**Purpose:** {kb}\n\n"
                f"**Usage:** Enter `{base_cmd}` at the z/TPF operator console."
            )
        return ""

    output_fields = "\n".join(f"  • {f}" for f in detail.get("output_fields", []))
    rc_lines = "\n".join(
        f"  • {code}: {desc}" for code, desc in detail.get("rc_codes", {}).items()
    )
    parts = [
        f"**Command:** {base_cmd}",
        f"**Purpose:** {detail['purpose']}",
        f"**Category:** {detail['category']}",
        "",
        f"**Syntax:** `{detail['syntax']}`",
        "",
        f"**Description:**\n{detail['description']}",
        "",
        f"**Expected Response / Output Fields:**\n{output_fields}",
    ]
    if rc_lines:
        parts.extend(["", f"**Return Codes:**\n{rc_lines}"])
    parts.extend([
        "",
        f"**Example:** `{detail.get('example', base_cmd)}`",
        "",
        "**When to Use:** "
        f"For {detail['category'].lower()} monitoring and troubleshooting. "
        "Correlate with ZSTAT and ZLOG for a full operational picture.",
    ])
    if detail.get("tos_note"):
        parts.extend(["", f"**TOS / RAVEN:** {detail['tos_note']}"])
    return "\n".join(parts)


def stream_text_chunks(text: str, chunk_size: int = 64):
    """Yield text in chunks for SSE streaming."""
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]
