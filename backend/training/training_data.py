"""
STS Coder — Extended ZTPF Training Data with Z Command Entries
"""

TRAINING_SAMPLES = [
    # ── 1. File Access Entry ──
    {
        "entry_text": """TR00     CSECT
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLI   0(R3),C'A'
         BNE   ERR0010
         MVC   WORK_LOC,INPUT_LOC
         FILEC R4,LEV=1,TYPE=FACE
         LTR   R15,R15
         BNZ   ERR0020
         MVC   OUTPUT_DATA,0(R4)
         EXITC TRDR""",
        "entry_type": "FILE_ACCESS",
        "purpose": "File access and record retrieval",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": True,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False},
    },
    # ── 2. PNR Processing ──
    {
        "entry_text": """PNRFETCH CSECT
         USING *,R12
         ENTER TRDR
         L     R5,CE1CR0
         PNRCC TYPE=A
         LTR   R15,R15
         BNZ   PNRERR
         MVC   OUT_PNR,PNR_DATA
         EXITC TRDR
PNRERR   DS    0H
         MVI   ERR_CODE,C'P'
         BACKC TRDR""",
        "entry_type": "PNR_PROCESSING",
        "purpose": "PNR processing",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": True, "has_service": False},
    },
    # ── 3. Service Call ──
    {
        "entry_text": """SVCPROC  CSECT
         USING *,R12
         ENTER TRDR
         LA    R3,SVCAREA
         MVC   SVC_REQ(20),INPUT_BUF
         SERVC TYPE=SYNC,AREA=(R3)
         LTR   R15,R15
         BNZ   SVCFAIL
         MVC   RESP_DATA,SVC_RESP
         EXITC TRDR
SVCFAIL  DS    0H
         MVI   ERR_FLAG,X'FF'
         BACKC TRDR""",
        "entry_type": "SERVICE_CALL",
        "purpose": "Service call processing",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": True},
    },
    # ── 4. Record Creation ──
    {
        "entry_text": """RECCRT   CSECT
         USING *,R12
         ENTER TRDR
         LA    R4,RECAREA
         MVC   REC_ID,INPUT_ID
         MVC   REC_NAME,INPUT_NAME
         CRUSA TYPE=NEW,AREA=(R4),LEN=256
         LTR   R15,R15
         BNZ   CRTERR
         ST    R4,RECPTR
         EXITC TRDR
CRTERR   MVI   ERR_CODE,C'C'
         BACKC TRDR""",
        "entry_type": "RECORD_CREATION",
        "purpose": "Record creation / update processing",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 5. Validation Entry ──
    {
        "entry_text": """VALCHK   CSECT
         USING *,R12
         ENTER TRDR
         L     R3,INPUT_PTR
         CLI   0(R3),X'00'
         BE    INVALID
         CLC   0(6,R3),=C'000000'
         BE    INVALID
         CLI   5(R3),C' '
         BNE   VALID
INVALID  DS    0H
         MVI   RESULT,C'N'
         B     DONE
VALID    DS    0H
         MVI   RESULT,C'Y'
DONE     DS    0H
         EXITC TRDR""",
        "entry_type": "VALIDATION",
        "purpose": "Input validation and field checking",
        "risk_level": "LOW",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": False,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 6. Storage Management ──
    {
        "entry_text": """STGMGR   CSECT
         USING *,R12
         ENTER TRDR
         GETCC R4,LEN=4096
         LTR   R15,R15
         BNZ   STGERR
         ST    R4,WORK_PTR
         MVC   0(256,R4),INPUT_BUF
         GLOBZ SET,AREA=(R4)
         RELCC (R4)
         EXITC TRDR
STGERR   MVI   ERR_CODE,C'S'
         BACKC TRDR""",
        "entry_type": "STORAGE_MANAGEMENT",
        "purpose": "Storage allocation and management",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 7. Z ENTRY Command Processing ──
    {
        "entry_text": """ZCMDPROC CSECT
* Z ENTRY DISPLAY/MODIFY OPERATOR COMMAND HANDLER
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Parse Z command verb from input
         MVC   ZCMD_VERB(8),0(R3)
         CLI   ZCMD_VERB,C'E'
         BE    Z_ENTRY_CMD
         CLI   ZCMD_VERB,C'T'
         BE    Z_TRANS_CMD
         CLI   ZCMD_VERB,C'P'
         BE    Z_PROG_CMD
         B     Z_UNKNOWN
Z_ENTRY_CMD DS  0H
         MVC   Z_RESP(40),=CL40'Z ENTRY: PROCESSING...'
         B     Z_RESPOND
Z_TRANS_CMD DS  0H
         MVC   Z_RESP(40),=CL40'Z TRANS: PROCESSING...'
         B     Z_RESPOND
Z_PROG_CMD  DS  0H
         MVC   Z_RESP(40),=CL40'Z PROG: PROCESSING...'
         B     Z_RESPOND
Z_UNKNOWN   DS  0H
         MVI   ERR_CODE,C'Z'
         BACKC TRDR
Z_RESPOND   DS  0H
         SENDC TYPE=RESP,DATA=Z_RESP
         EXITC TRDR
ZCMD_VERB   DS  CL8
Z_RESP      DS  CL40
ERR_CODE    DS  CL4""",
        "entry_type": "Z_COMMAND_HANDLER",
        "purpose": "ZTPF Z operator command processing",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False},
    },
    # ── 8. Z TPFDF File Management Command ──
    {
        "entry_text": """ZTPFDF   CSECT
* Z TPFDF — TPF Data Facility operator interface
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Check for TPFDF subcommand
         CLC   0(6,R3),=C'TPFDF '
         BNE   NOT_TPFDF
         MVC   SUBCMD,6(R3)
         CLI   SUBCMD,C'L'
         BE    TPFDF_LIST
         CLI   SUBCMD,C'D'
         BE    TPFDF_DISP
         B     TPFDF_HELP
TPFDF_LIST DS  0H
         FILEC R4,LEV=1,TYPE=TPFD
         LTR   R15,R15
         BNZ   TPFDF_ERR
         MVC   DISP_DATA,0(R4)
         SENDC TYPE=RESP,DATA=DISP_DATA
         B     TPFDF_END
TPFDF_DISP  DS  0H
         FINDA R5,LEV=2,TYPE=TPFD
         LTR   R15,R15
         BNZ   TPFDF_ERR
         MVC   DISP_DATA,0(R5)
         SENDC TYPE=RESP,DATA=DISP_DATA
         B     TPFDF_END
TPFDF_HELP  DS  0H
         MVC   DISP_DATA,=CL80'Z TPFDF: L=LIST D=DISPLAY'
         SENDC TYPE=RESP,DATA=DISP_DATA
         B     TPFDF_END
TPFDF_ERR   DS  0H
         MVI   ERR_CODE,C'D'
         BACKC TRDR
NOT_TPFDF   DS  0H
         MVI   ERR_CODE,C'N'
         BACKC TRDR
TPFDF_END   DS  0H
         EXITC TRDR
SUBCMD      DS  CL4
DISP_DATA   DS  CL80
ERR_CODE    DS  CL4""",
        "entry_type": "Z_TPFDF_COMMAND",
        "purpose": "Z TPFDF TPF Data Facility operator command",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": True,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False},
    },
    # ── 9. Z STAT Performance Statistics ──
    {
        "entry_text": """ZSTATPROC CSECT
* Z STAT — Performance statistics reporting entry
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         MVC   STAT_KEY,0(R3)
         CLC   STAT_KEY(4),=C'STAT'
         BNE   STAT_ERR
         GETCC R4,LEN=512
         LTR   R15,R15
         BNZ   STAT_ERR
         MVC   0(8,R4),=CL8'STATHDR '
         AP    STAT_CNT(4),=P'1'
         CVD   R5,DBLWORD
         MVC   STAT_OUT,EDPAT
         ED    STAT_OUT,DBLWORD+4
         SENDC TYPE=RESP,DATA=0(R4)
         RELCC (R4)
         EXITC TRDR
STAT_ERR  DS   0H
         MVI   ERR_CODE,C'S'
         BACKC TRDR
STAT_KEY  DS   CL8
STAT_CNT  DC   PL4'0'
STAT_OUT  DS   CL20
DBLWORD   DS   D
EDPAT     DC   XL12'402020202020202020202120'
ERR_CODE  DS   CL4""",
        "entry_type": "Z_STAT_COMMAND",
        "purpose": "Z STAT performance statistics collection",
        "risk_level": "LOW",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 10. REXX/RAVEN Exec Entry ──
    {
        "entry_text": """/* IBM z/TPF REXX RAVEN Exec — Entry Processing */
/* Entry: TRAVPROC — Travel booking processor    */
ADDRESS RAVEN

PARSE ARG entry_input

/* Validate input */
IF entry_input = '' THEN DO
  SAY 'ERR: No input provided'
  EXIT 8
END

/* Extract booking reference */
booking_ref = SUBSTR(entry_input, 1, 6)
pax_name    = STRIP(SUBSTR(entry_input, 7, 20))

/* Call TPF service */
CALL_RESULT = ''
ADDRESS RAVEN 'SERVC TYPE=BOOKING,REF='booking_ref
IF RC ^= 0 THEN DO
  SAY 'ERR: Service call failed RC='RC
  EXIT RC
END

/* Process response */
SAY 'OK: Booking 'booking_ref' processed for 'pax_name
EXIT 0""",
        "entry_type": "REXX_RAVEN_EXEC",
        "purpose": "IBM z/TPF REXX RAVEN exec for booking processing",
        "risk_level": "MODERATE",
        "features": {"has_enter": False, "has_exit": False, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": True},
    },
    # ── 11. Z DUMP Command Handler ──
    {
        "entry_text": """ZDUMPENT CSECT
* Z DUMP — Memory dump diagnostic command handler
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLC   0(4,R3),=C'DUMP'
         BNE   DUMP_ERR
         L     R4,4(R3)          Load dump address
         L     R5,8(R3)          Load dump length
         LTR   R5,R5
         BZ    DUMP_ERR
         CH    R5,=H'4096'
         BH    DUMP_ERR          Max 4K dump
         GETCC R6,LEN=256
         LTR   R15,R15
         BNZ   DUMP_ERR
         MVC   0(16,R6),=CL16'DUMP HEADER     '
         MVC   16(8,R6),DUMP_ID
         MVCL  R6,R4             Copy memory region
         SENDC TYPE=DUMP,AREA=(R6),LEN=(R5)
         RELCC (R6)
         EXITC TRDR
DUMP_ERR  DS   0H
         MVI   ERR_CODE,C'D'
         BACKC TRDR
DUMP_ID   DS   CL8
ERR_CODE  DS   CL4""",
        "entry_type": "Z_DUMP_COMMAND",
        "purpose": "Z DUMP diagnostic memory dump command",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 12. Multi-File Join ──
    {
        "entry_text": """MFJOIN   CSECT
         USING *,R12
         ENTER TRDR
         MVC   KEY1,INPUT_KEY
         FILEC R4,LEV=1,TYPE=CUST
         LTR   R15,R15
         BNZ   NFOUND1
         MVC   CUST_DATA,0(R4)
         MVC   KEY2,CUST_REF
         FINDA R5,LEV=2,TYPE=BOOKING
         LTR   R15,R15
         BNZ   NFOUND2
         MVC   BOOK_DATA,0(R5)
         MVC   RESP_CUST,CUST_DATA
         MVC   RESP_BOOK,BOOK_DATA
         EXITC TRDR
NFOUND1  MVI   ERR_CODE,C'1'
         B     ERRXIT
NFOUND2  MVI   ERR_CODE,C'2'
ERRXIT   BACKC TRDR""",
        "entry_type": "MULTI_FILE_JOIN",
        "purpose": "Multi-file record join and retrieval",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": True,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 13. Z PAGE Command Handler ──
    {
        "entry_text": """ZPAGE    CSECT
* Z PAGE — Terminal paging operator command
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLC   0(4,R3),=C'PAGE'
         BNE   PAGE_ERR
         CLI   5(R3),C'F'
         BE    PAGE_FWD
         CLI   5(R3),C'B'
         BE    PAGE_BWD
         B     PAGE_HELP
PAGE_FWD DS    0H
         MVC   PAGE_RESP,=CL40'Z PAGE: SCROLLING FORWARD'
         B     PAGE_SEND
PAGE_BWD DS    0H
         MVC   PAGE_RESP,=CL40'Z PAGE: SCROLLING BACKWARD'
         B     PAGE_SEND
PAGE_HELP DS   0H
         MVC   PAGE_RESP,=CL40'Z PAGE: F=FWD B=BWD'
PAGE_SEND DS   0H
         SENDC TYPE=RESP,DATA=PAGE_RESP
         EXITC TRDR
PAGE_ERR DS    0H
         MVI   ERR_CODE,C'P'
         BACKC TRDR
PAGE_RESP DS   CL40
ERR_CODE  DS   CL4""",
        "entry_type": "Z_PAGE_COMMAND",
        "purpose": "Z PAGE terminal paging operator command",
        "risk_level": "LOW",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 14. Z D0DB Command Handler ──
    {
        "entry_text": """ZD0DB    CSECT
* Z D0DB — Database operator command
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLC   0(4,R3),=C'D0DB'
         BNE   DB_ERR
         CLI   5(R3),C'S'
         BE    DB_START
         CLI   5(R3),C'P'
         BE    DB_STOP
         B     DB_HELP
DB_START DS    0H
         MVC   DB_RESP,=CL40'Z D0DB: DATABASE STARTED'
         B     DB_SEND
DB_STOP  DS    0H
         MVC   DB_RESP,=CL40'Z D0DB: DATABASE STOPPED'
         B     DB_SEND
DB_HELP  DS    0H
         MVC   DB_RESP,=CL40'Z D0DB: S=START P=STOP'
DB_SEND  DS    0H
         SENDC TYPE=RESP,DATA=DB_RESP
         EXITC TRDR
DB_ERR   DS    0H
         MVI   ERR_CODE,C'D'
         BACKC TRDR
DB_RESP  DS    CL40
ERR_CODE DS    CL4""",
        "entry_type": "Z_D0DB_COMMAND",
        "purpose": "Z D0DB database operator command",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 15. Z FILE Command Handler ──
    {
        "entry_text": """ZFILE    CSECT
* Z FILE — File system operator command
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLC   0(4,R3),=C'FILE'
         BNE   FILE_ERR
         B     FILE_SEND
FILE_SEND DS   0H
         MVC   FILE_RESP,=CL40'Z FILE: FILE SYSTEM STATUS DISPLAY'
         SENDC TYPE=RESP,DATA=FILE_RESP
         EXITC TRDR
FILE_ERR DS    0H
         MVI   ERR_CODE,C'F'
         BACKC TRDR
FILE_RESP DS   CL40
ERR_CODE  DS   CL4""",
        "entry_type": "Z_FILE_COMMAND",
        "purpose": "Z FILE file system operator command",
        "risk_level": "LOW",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 16. Z INET Command Handler ──
    {
        "entry_text": """ZINET    CSECT
* Z INET — Internet Daemon operator command
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         CLC   0(4,R3),=C'INET'
         BNE   INET_ERR
         B     INET_SEND
INET_SEND DS   0H
         MVC   INET_RESP,=CL40'Z INET: SOCKET AND DAEMON STATUS'
         SENDC TYPE=RESP,DATA=INET_RESP
         EXITC TRDR
INET_ERR DS    0H
         MVI   ERR_CODE,C'I'
         BACKC TRDR
INET_RESP DS   CL40
ERR_CODE  DS   CL4""",
        "entry_type": "Z_INET_COMMAND",
        "purpose": "Z INET internet daemon operator command",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False},
    },
]


FEATURE_PATTERNS = {
    "has_enter":           r"\bENTER\b|\bENTRC\b|\bENPTS\b",
    "has_exit":            r"\bEXITC\b|\bEXITN\b|\bBACKC\b|\bBACK\b",
    "has_filec":           r"\bFILEC\b|\bFILEM\b|\bFINDA\b|\bFINDC\b",
    "has_validation":      r"\bCLI\b|\bCLC\b|\bTM\b|\bCP\b",
    "has_error_handling":  r"\bERR\w*\b|\bFAIL\b|\bINVALID\b|\bABORT\b",
    "has_ecb":             r"\bECB\w*\b|\bCE1CR0\b",
    "has_pnr":             r"\bPNRCC\b|\bPNRAC\b",
    "has_service":         r"\bSERVC\b|\bSVCRC\b",
    "has_storage_get":     r"\bGETCC\b|\bGETFC\b|\bALASC\b",
    "has_storage_rel":     r"\bRELCC\b|\bRELFC\b|\bRLASC\b",
    "has_timer":           r"\bTIMEC\b",
    "has_send":            r"\bSENDC\b|\bSENDM\b",
    "has_arithmetic":      r"\bAP\b|\bSP\b|\bMP\b|\bDP\b|\bZAP\b|\bCVD\b|\bCVB\b",
    "has_crusa":           r"\bCRUSA\b|\bCRUSC\b",
    "has_globz":           r"\bGLOBZ\b|\bGLOBS\b",
    "has_z_command":       r"\bZ\s+(?:ENTRY|TPFDF|DUMP|STAT|TRAP|TRANS|PROG|SSBP)\b|ADDRESS\s+RAVEN",
    "has_rexx":            r"ADDRESS\s+RAVEN|PARSE\s+ARG|SAY\s+|CALL_RESULT",
}

ENTRY_TYPES = [
    "FILE_ACCESS", "PNR_PROCESSING", "SERVICE_CALL", "RECORD_CREATION",
    "VALIDATION", "TIMER_PROCESSING", "MESSAGE_HANDLING", "STORAGE_MANAGEMENT",
    "DATA_TRANSFORMATION", "MULTI_FILE_JOIN", "GENERAL_PROCESSING",
    "Z_COMMAND_HANDLER", "Z_TPFDF_COMMAND", "Z_STAT_COMMAND",
    "Z_DUMP_COMMAND", "REXX_RAVEN_EXEC", "Z_PAGE_COMMAND", "Z_D0DB_COMMAND",
    "Z_FILE_COMMAND", "Z_INET_COMMAND"
]

RISK_LEVELS = ["LOW", "MODERATE", "HIGH"]
