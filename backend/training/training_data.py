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
    # ── 16. File Lock (FIWHC/UNFRC) ──
    {
        "entry_text": """FLLOCK   CSECT
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
         FIWHC R4,LEV=1,TYPE=PNRDB
         LTR   R15,R15
         BNZ   LOCKERR
         MVC   WORK,0(R4)
         UNFRC R4
         EXITC TRDR
LOCKERR  MVI   ERR_CODE,C'L'
         BACKC TRDR
WORK     DS    CL256
ERR_CODE DS    CL4""",
        "entry_type": "FILE_ACCESS",
        "purpose": "File record lock and release with FIWHC/UNFRC",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": True,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False},
    },
    # ── 17. Storage leak risk (GETCC no RELCC) ──
    {
        "entry_text": """STGLEAK  CSECT
         USING *,R12
         ENTER TRDR
         GETCC R4,LEN=2048
         LTR   R15,R15
         BNZ   STGERR
         MVC   0(80,R4),INPUT_BUF
         EXITC TRDR
STGERR   BACKC TRDR
INPUT_BUF DS   CL80""",
        "entry_type": "STORAGE_MANAGEMENT",
        "purpose": "Storage allocation without RELCC (leak pattern)",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False,
                     "has_storage_get": True, "has_storage_rel": False},
    },
    # ── 18. TOS REXX monitoring exec ──
    {
        "entry_text": """/* REXX — TOS health check */
ADDRESS RAVEN
PARSE ARG sys_id
'ZOSRV DISPLAY'
IF RC \\= 0 THEN EXIT 8
'ZDSYS ALL'
IF RC \\= 0 THEN EXIT 4
'ZDTCP DISPLAY'
SAY 'TOS automation check complete for' sys_id
EXIT 0""",
        "entry_type": "REXX_RAVEN_EXEC",
        "purpose": "TOS automation health monitoring via RAVEN",
        "risk_level": "LOW",
        "features": {"has_enter": False, "has_exit": False, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False,
                     "has_rexx": True, "has_z_command": True},
    },
    # ── 19. Z PING network check ──
    {
        "entry_text": """/* REXX TOS network ping */
ADDRESS RAVEN
PARSE ARG host
IF host = '' THEN EXIT 8
'ZPING' host
IF RC \\= 0 THEN SAY 'PING failed RC='RC
ELSE SAY 'PING OK for' host
EXIT RC""",
        "entry_type": "REXX_RAVEN_EXEC",
        "purpose": "TOS network connectivity check via ZPING",
        "risk_level": "LOW",
        "features": {"has_rexx": True, "has_z_command": True, "has_validation": True,
                     "has_error_handling": True, "has_enter": False, "has_exit": False,
                     "has_filec": False, "has_ecb": False, "has_pnr": False, "has_service": False},
    },
    # ── 20. Z INET Command Handler ──
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
    # ── 21. RAVEN IPL Automation ──
    {
        "entry_text": """/* REXX — RAVEN IPL Automation Script */
/* Automates IPL verification and system readiness checks */
ADDRESS RAVEN

PARSE ARG sys_target ipl_type

IF sys_target = '' THEN DO
  SAY 'ERR: System target required for IPL automation'
  EXIT 8
END

/* Initiate IPL verification sequence */
SAY 'IPL AUTOMATION: Verifying system' sys_target 'type' ipl_type

ADDRESS RAVEN 'ZIPL STATUS' sys_target
IF RC \\= 0 THEN DO
  SAY 'ERR: IPL status check failed RC='RC
  EXIT RC
END

/* Validate post-IPL system state */
ADDRESS RAVEN 'ZDSYS' sys_target
IF RC \\= 0 THEN DO
  SAY 'WARN: System display returned RC='RC
  EXIT 4
END

/* Confirm core table loads */
ADDRESS RAVEN 'ZCTBL VERIFY'
IF RC \\= 0 THEN DO
  SAY 'ERR: Core table verification failed RC='RC
  EXIT 12
END

SAY 'IPL AUTOMATION: System' sys_target 'verified successfully'
EXIT 0""",
        "entry_type": "IPL_AUTOMATION",
        "purpose": "RAVEN IPL automation and post-IPL verification",
        "risk_level": "HIGH",
        "features": {"has_enter": False, "has_exit": False, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False,
                     "has_rexx": True, "has_z_command": True},
    },
    # ── 22. ECB Monitoring Entry ──
    {
        "entry_text": """ECBMON   CSECT
* ECB Monitoring — ZDECB cleanup and resource tracking
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Check ECB allocation state
         CLI   0(R3),X'80'
         BE    ECBFREE
         CLI   0(R3),X'40'
         BE    ECBINUSE
         B     ECBERR
ECBINUSE DS    0H
* Allocate work storage for ECB snapshot
         GETCC R4,LEN=1024
         LTR   R15,R15
         BNZ   ECBERR
* Capture ECB state data
         MVC   0(64,R4),0(R3)
         MVC   64(8,R4),=CL8'ECBSNAP '
* Release work storage after capture
         RELCC (R4)
         MVC   ECB_RESP,=CL40'ZDECB: ECB IN USE — SNAPSHOT TAKEN'
         B     ECBSEND
ECBFREE  DS    0H
         MVC   ECB_RESP,=CL40'ZDECB: ECB FREE — NO CLEANUP NEEDED'
         B     ECBSEND
ECBSEND  DS    0H
         SENDC TYPE=RESP,DATA=ECB_RESP
         EXITC TRDR
ECBERR   DS    0H
         MVI   ERR_CODE,C'E'
         BACKC TRDR
ECB_RESP DS    CL40
ERR_CODE DS    CL4""",
        "entry_type": "ECB_MONITORING",
        "purpose": "ECB monitoring with ZDECB cleanup and GETCC/RELCC paired storage",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False,
                     "has_storage_get": True, "has_storage_rel": True},
    },
    # ── 23. TPFDF Schema Validation Entry ──
    {
        "entry_text": """TPFVAL   CSECT
* TPFDF Schema Validation — Z TPFDF SCHEMA / FINDA integrity check
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Parse schema identifier from operator input
         CLC   0(6,R3),=C'SCHEMA'
         BNE   SCHMERR
         MVC   SCHM_ID,7(R3)
* Locate schema definition record via FINDA
         FINDA R4,LEV=1,TYPE=TPFD
         LTR   R15,R15
         BNZ   SCHMISS
* Validate schema structure fields
         CLC   0(4,R4),=C'SCHM'
         BNE   SCHMERR
         CLI   4(R4),X'00'
         BE    SCHMERR
         CLC   5(2,R4),=H'0'
         BE    SCHMERR
* Schema is valid
         MVC   SCHM_RESP,=CL80'Z TPFDF SCHEMA: VALID'
         SENDC TYPE=RESP,DATA=SCHM_RESP
         EXITC TRDR
SCHMISS  DS    0H
         MVC   SCHM_RESP,=CL80'Z TPFDF SCHEMA: NOT FOUND'
         SENDC TYPE=RESP,DATA=SCHM_RESP
         EXITC TRDR
SCHMERR  DS    0H
         MVI   ERR_CODE,C'V'
         BACKC TRDR
SCHM_ID   DS   CL8
SCHM_RESP DS   CL80
ERR_CODE  DS   CL4""",
        "entry_type": "TPFDF_VALIDATION",
        "purpose": "TPFDF schema validation with FINDA record lookup",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": True,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False},
    },
    # ── 24. Network Health Check REXX ──
    {
        "entry_text": """/* REXX — Network Health Check via ZPING / ZDTCP */
/* Validates connectivity to all configured endpoints */
ADDRESS RAVEN

PARSE ARG host_list

IF host_list = '' THEN DO
  SAY 'ERR: Host list required. Usage: NETHCHK host1,host2,...'
  EXIT 8
END

fail_count = 0
pass_count = 0

DO WHILE host_list \\= ''
  PARSE VAR host_list current_host ',' host_list
  current_host = STRIP(current_host)
  IF current_host = '' THEN ITERATE

  /* Ping test */
  'ZPING' current_host
  IF RC \\= 0 THEN DO
    SAY 'FAIL: ZPING' current_host 'RC='RC
    fail_count = fail_count + 1
    ITERATE
  END

  /* TCP stack verification */
  'ZDTCP DISPLAY' current_host
  IF RC \\= 0 THEN DO
    SAY 'WARN: ZDTCP' current_host 'RC='RC
    fail_count = fail_count + 1
    ITERATE
  END

  SAY 'PASS:' current_host 'network OK'
  pass_count = pass_count + 1
END

SAY 'NETWORK CHECK COMPLETE: PASS='pass_count 'FAIL='fail_count
IF fail_count > 0 THEN EXIT 4
EXIT 0""",
        "entry_type": "NETWORK_CHECK",
        "purpose": "Network health check using ZPING and ZDTCP",
        "risk_level": "LOW",
        "features": {"has_enter": False, "has_exit": False, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False,
                     "has_rexx": True, "has_z_command": True},
    },
    # ── 25. ZDUPD — Dynamic Program Update Handler ──
    {
        "entry_text": """ZDUPDHND CSECT
* ZDUPD — Dynamic program update handler
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Parse ZDUPD subcommand
         CLC   0(5,R3),=C'ZDUPD'
         BNE   DUPDERR
         CLI   6(R3),C'L'
         BE    DUPD_LOAD
         CLI   6(R3),C'D'
         BE    DUPD_DROP
         CLI   6(R3),C'S'
         BE    DUPD_STAT
         B     DUPD_HELP
DUPD_LOAD DS   0H
         MVC   DUPD_PGM,8(R3)
* Allocate staging area for program load
         GETCC R4,LEN=4096
         LTR   R15,R15
         BNZ   DUPDERR
         MVC   0(8,R4),DUPD_PGM
         MVC   8(32,R4),=CL32'DYNAMIC LOAD IN PROGRESS'
         RELCC (R4)
         MVC   DUPD_RESP,=CL40'ZDUPD: PROGRAM LOADED'
         B     DUPDSEND
DUPD_DROP DS   0H
         MVC   DUPD_RESP,=CL40'ZDUPD: PROGRAM DROPPED'
         B     DUPDSEND
DUPD_STAT DS   0H
         MVC   DUPD_RESP,=CL40'ZDUPD: STATUS DISPLAYED'
         B     DUPDSEND
DUPD_HELP DS   0H
         MVC   DUPD_RESP,=CL40'ZDUPD: L=LOAD D=DROP S=STATUS'
DUPDSEND DS    0H
         SENDC TYPE=RESP,DATA=DUPD_RESP
         EXITC TRDR
DUPDERR  DS    0H
         MVI   ERR_CODE,C'U'
         BACKC TRDR
DUPD_PGM  DS   CL8
DUPD_RESP DS   CL40
ERR_CODE  DS   CL4""",
        "entry_type": "ZDUPD_HANDLER",
        "purpose": "ZDUPD dynamic program update load/drop/status handler",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False,
                     "has_storage_get": True, "has_storage_rel": True},
    },
    # ── 26. Storage Pool Monitor Entry ──
    {
        "entry_text": """STGPOOL  CSECT
* Storage Pool Monitor — GETCC/RELCC tracking with ZPOOL reporting
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Allocate monitoring block
         GETCC R4,LEN=2048
         LTR   R15,R15
         BNZ   POOLERR
         MVC   0(8,R4),=CL8'POOLHDR '
* Capture pool statistics
         GETCC R5,LEN=512
         LTR   R15,R15
         BNZ   POOL_REL1
         MVC   0(8,R5),=CL8'POOLSTAT'
         AP    POOL_CNT(4),=P'1'
         CVD   R6,DBLWORD
         MVC   POOL_OUT,EDPAT
         ED    POOL_OUT,DBLWORD+4
         MVC   8(20,R5),POOL_OUT
* Release stat block
         RELCC (R5)
* Send pool report
         MVC   64(40,R4),=CL40'ZPOOL: STORAGE POOL STATUS CAPTURED'
         SENDC TYPE=RESP,DATA=0(R4)
* Release monitoring block
         RELCC (R4)
         EXITC TRDR
POOL_REL1 DS   0H
         RELCC (R4)
POOLERR  DS    0H
         MVI   ERR_CODE,C'P'
         BACKC TRDR
POOL_CNT  DC   PL4'0'
POOL_OUT  DS   CL20
DBLWORD   DS   D
EDPAT     DC   XL12'402020202020202020202120'
ERR_CODE  DS   CL4""",
        "entry_type": "STORAGE_MONITOR",
        "purpose": "Storage pool monitoring with paired GETCC/RELCC and ZPOOL reporting",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": False, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False,
                     "has_storage_get": True, "has_storage_rel": True,
                     "has_arithmetic": True, "has_send": True},
    },
    # ── 27. Message Queue Handler ──
    {
        "entry_text": """MSGQHND  CSECT
* Message Queue Handler — SENDC/RECVC with message correlation
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Extract message correlation ID
         MVC   MSG_CORR,0(R3)
         CLI   MSG_CORR,X'00'
         BE    MSGERR
* Receive inbound message
         RECVC R4,TYPE=QUEUE,CORR=MSG_CORR
         LTR   R15,R15
         BNZ   MSGFAIL
* Validate message payload
         CLC   0(4,R4),=C'MSGP'
         BNE   MSGFMT
* Process message content
         MVC   MSG_DATA,4(R4)
         MVC   MSG_RESP(8),=CL8'ACK     '
         MVC   MSG_RESP+8(8),MSG_CORR
* Send acknowledgement
         SENDC TYPE=ACK,DATA=MSG_RESP,CORR=MSG_CORR
         LTR   R15,R15
         BNZ   MSGFAIL
         EXITC TRDR
MSGFMT   DS    0H
         MVI   ERR_CODE,C'F'
         B     MSGEXIT
MSGFAIL  DS    0H
         MVI   ERR_CODE,C'Q'
         B     MSGEXIT
MSGERR   DS    0H
         MVI   ERR_CODE,C'C'
MSGEXIT  DS    0H
         BACKC TRDR
MSG_CORR  DS   CL8
MSG_DATA  DS   CL256
MSG_RESP  DS   CL16
ERR_CODE  DS   CL4""",
        "entry_type": "MESSAGE_HANDLER",
        "purpose": "Message queue handler with SENDC/RECVC and correlation ID tracking",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False,
                     "has_send": True},
    },
    # ── 28. Timer-Driven Automation ──
    {
        "entry_text": """TIMRAUTO CSECT
* Timer-Driven Automation — TIMEC periodic scheduling
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Check if this is a timer-driven invocation
         CLI   0(R3),C'T'
         BE    TIM_SCHED
         CLI   0(R3),C'C'
         BE    TIM_CANCEL
         B     TIM_STATUS
TIM_SCHED DS   0H
* Schedule periodic timer at 30-second intervals
         TIMEC TYPE=REL,BIN=30,ECB=TIMECB
         LTR   R15,R15
         BNZ   TIMERR
* Allocate timer state block
         GETCC R4,LEN=256
         LTR   R15,R15
         BNZ   TIMERR
         MVC   0(8,R4),=CL8'TIMSTATE'
         AP    TIM_CNT(4),=P'1'
         CVD   R5,DBLWORD
         MVC   TIM_OUT,EDPAT
         ED    TIM_OUT,DBLWORD+4
         MVC   8(20,R4),TIM_OUT
         RELCC (R4)
         MVC   TIM_RESP,=CL40'TIMEC: SCHEDULED INTERVAL=30S'
         B     TIMSEND
TIM_CANCEL DS  0H
         MVC   TIM_RESP,=CL40'TIMEC: TIMER CANCELLED'
         B     TIMSEND
TIM_STATUS DS  0H
         MVC   TIM_RESP,=CL40'TIMEC: TIMER STATUS DISPLAYED'
TIMSEND  DS    0H
         SENDC TYPE=RESP,DATA=TIM_RESP
         EXITC TRDR
TIMERR   DS    0H
         MVI   ERR_CODE,C'T'
         BACKC TRDR
TIMECB    DS   F
TIM_CNT   DC   PL4'0'
TIM_OUT   DS   CL20
DBLWORD   DS   D
EDPAT     DC   XL12'402020202020202020202120'
TIM_RESP  DS   CL40
ERR_CODE  DS   CL4""",
        "entry_type": "TIMER_AUTOMATION",
        "purpose": "Timer-driven automation with TIMEC periodic scheduling",
        "risk_level": "MODERATE",
        "features": {"has_enter": True, "has_exit": True, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False,
                     "has_timer": True, "has_storage_get": True,
                     "has_storage_rel": True, "has_arithmetic": True,
                     "has_send": True},
    },
    # ── 29. Multi-Step Recovery REXX ──
    {
        "entry_text": """/* REXX — Multi-Step Recovery with Retry Logic and Escalation */
/* Entry: RECOVPROC — Automated recovery with graduated response */
ADDRESS RAVEN

PARSE ARG target_entry max_retries

IF target_entry = '' THEN DO
  SAY 'ERR: Target entry required for recovery'
  EXIT 8
END

IF max_retries = '' THEN max_retries = 3

retry_count = 0
recovery_ok = 0

/* Retry loop with escalation */
DO WHILE retry_count < max_retries & recovery_ok = 0
  retry_count = retry_count + 1
  SAY 'RECOVERY: Attempt' retry_count 'of' max_retries 'for' target_entry

  /* Step 1: Attempt soft restart */
  ADDRESS RAVEN 'ZRSRT SOFT' target_entry
  IF RC = 0 THEN DO
    SAY 'RECOVERY: Soft restart succeeded on attempt' retry_count
    recovery_ok = 1
    LEAVE
  END

  /* Step 2: Wait before escalation */
  SAY 'RECOVERY: Soft restart failed RC='RC', waiting 5s...'
  ADDRESS RAVEN 'ZWAIT 5'

  /* Step 3: Escalate to hard restart on final attempt */
  IF retry_count = max_retries THEN DO
    SAY 'RECOVERY: Escalating to hard restart for' target_entry
    ADDRESS RAVEN 'ZRSRT HARD' target_entry
    IF RC = 0 THEN DO
      SAY 'RECOVERY: Hard restart succeeded'
      recovery_ok = 1
    END
    ELSE DO
      SAY 'ERR: Hard restart failed RC='RC
    END
  END
END

IF recovery_ok = 0 THEN DO
  SAY 'ERR: All recovery attempts exhausted for' target_entry
  EXIT 12
END

SAY 'RECOVERY: Complete for' target_entry
EXIT 0""",
        "entry_type": "RECOVERY_AUTOMATION",
        "purpose": "Multi-step recovery automation with retry logic and escalation",
        "risk_level": "HIGH",
        "features": {"has_enter": False, "has_exit": False, "has_filec": False,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": False, "has_pnr": False, "has_service": False,
                     "has_rexx": True, "has_z_command": True},
    },
    # ── 30. File Corruption Validation Entry ──
    {
        "entry_text": """FILEVAL  CSECT
* File Corruption Validation — CRC check with FINDA / FILEC
         USING *,R12
         ENTER TRDR
         L     R3,CE1CR0
* Parse file reference from input
         MVC   FILE_REF,0(R3)
         CLI   FILE_REF,X'00'
         BE    FVERR
* Read primary record via FILEC
         FILEC R4,LEV=1,TYPE=CUST
         LTR   R15,R15
         BNZ   FVNFND
* Compute CRC over record data
         LA    R5,0(R4)
         LA    R6,256
         SR    R7,R7
CRCLOOP  DS    0H
         IC    R8,0(R5)
         AR    R7,R8
         LA    R5,1(R5)
         BCT   R6,CRCLOOP
* Store computed CRC
         ST    R7,CRC_CALC
* Read stored CRC via FINDA
         FINDA R9,LEV=2,TYPE=CRCF
         LTR   R15,R15
         BNZ   FVCRCMISS
* Compare computed vs stored CRC
         CLC   CRC_CALC(4),0(R9)
         BNE   FVCRCFAIL
* CRC match — file integrity OK
         MVC   FV_RESP,=CL80'FILE VALIDATION: CRC OK — INTEGRITY VERIFIED'
         SENDC TYPE=RESP,DATA=FV_RESP
         EXITC TRDR
FVCRCFAIL DS   0H
         MVC   FV_RESP,=CL80'FILE VALIDATION: CRC MISMATCH — CORRUPTION'
         SENDC TYPE=RESP,DATA=FV_RESP
         MVI   ERR_CODE,C'X'
         BACKC TRDR
FVCRCMISS DS   0H
         MVC   FV_RESP,=CL80'FILE VALIDATION: STORED CRC NOT FOUND'
         SENDC TYPE=RESP,DATA=FV_RESP
         MVI   ERR_CODE,C'M'
         BACKC TRDR
FVNFND   DS    0H
         MVI   ERR_CODE,C'N'
         BACKC TRDR
FVERR    DS    0H
         MVI   ERR_CODE,C'E'
         BACKC TRDR
FILE_REF  DS   CL8
CRC_CALC  DS   F
FV_RESP   DS   CL80
ERR_CODE  DS   CL4""",
        "entry_type": "FILE_VALIDATION",
        "purpose": "File corruption validation with CRC check, FINDA and FILEC",
        "risk_level": "HIGH",
        "features": {"has_enter": True, "has_exit": True, "has_filec": True,
                     "has_validation": True, "has_error_handling": True,
                     "has_ecb": True, "has_pnr": False, "has_service": False,
                     "has_send": True},
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
    "has_z_command":       r"\bZ\s+(?:ENTRY|TPFDF|DUMP|STAT|TRAP|TRANS|PROG|SSBP|OSRV|DTCP|INET|PAGE|D0DB|FILE)\b|ADDRESS\s+RAVEN|'Z[A-Z]{3,}",
    "has_fiwhc":           r"\bFIWHC\b",
    "has_unfrc":           r"\bUNFRC\b",
    "has_rexx":            r"ADDRESS\s+RAVEN|PARSE\s+ARG|SAY\s+|CALL_RESULT",
    "has_critical_op":     r"\b(?:ZSTOP|ZSHUT|ZFCRZ|ZIPL|ZRSRT|ZDUPD|ZRSRT|HARD)\b",
    "has_database_op":     r"\b(?:ZTPFDF|ZFILE|ZPOOL|ZVOL|ZVAL|DBDEF|LREC)\b",
    "has_network_op":      r"\b(?:ZINET|ZDTCP|ZCONN|ZPING|ZLSA|ZNSDM|SOCKET|DAEMON)\b",
    "has_diagnostic_op":   r"\b(?:ZDBUG|ZCDSP|ZDECB|ZDUMP|ZTRAP|ZERR|ZLOG|TRACE|SNAP|PSW)\b",
    "has_security_op":     r"\b(?:ZKEY|ZNKEY|ZPWB|PASSWORD|ENCRYPTION)\b",
    "has_system_op":       r"\b(?:ZDSYS|ZSTAT|ZINFO|ZOPTS|ZONLN|ZATIM|ZDTIM|ZPROG)\b",
    "has_messaging_op":    r"\b(?:ZMQSC|ZMAIL|ZMTA|ZAWFS|MQSERIES|QUEUE|CHANNEL)\b",
    "has_storage_op":      r"\b(?:ZALOC|ZASER|ZCOMP|ZDSK|ZMOD|ZPATH|ZTAPE|ZTMON|VOLUME|DASD)\b",
}

ENTRY_TYPES = [
    "FILE_ACCESS", "PNR_PROCESSING", "SERVICE_CALL", "RECORD_CREATION",
    "VALIDATION", "TIMER_PROCESSING", "MESSAGE_HANDLING", "STORAGE_MANAGEMENT",
    "DATA_TRANSFORMATION", "MULTI_FILE_JOIN", "GENERAL_PROCESSING",
    "Z_COMMAND_HANDLER", "Z_TPFDF_COMMAND", "Z_STAT_COMMAND",
    "Z_DUMP_COMMAND", "REXX_RAVEN_EXEC", "Z_PAGE_COMMAND", "Z_D0DB_COMMAND",
    "Z_FILE_COMMAND", "Z_INET_COMMAND",
    "IPL_AUTOMATION", "ECB_MONITORING", "TPFDF_VALIDATION", "NETWORK_CHECK",
    "ZDUPD_HANDLER", "STORAGE_MONITOR", "MESSAGE_HANDLER", "TIMER_AUTOMATION",
    "RECOVERY_AUTOMATION", "FILE_VALIDATION",
]

RISK_LEVELS = ["LOW", "MODERATE", "HIGH"]
