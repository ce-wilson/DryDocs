"""Synthetic Control-M definition-XML fixtures for the xml_io round-trip suite.

BYTE LITERALS, DELIBERATELY. ``.gitattributes`` normalizes text EOLs, so a
committed CRLF ``.xml`` fixture would be silently rewritten and its test would
pass vacuously. Everything here is a ``bytes`` literal with explicit ``\\r\\n``,
BOM bytes and latin-1 bytes, written to ``tmp_path`` in BINARY mode by the tests.

Every value is invented (J18: reproducible anywhere, no company data). Each
fixture isolates one hazard; together they are the corpus test class A must
round-trip byte-identically — the test no serializer-based design can pass.
"""

from __future__ import annotations

#: F1 — happy path: one folder, one job, one variable.
F1_MINIMAL = b"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ1A">
    <VARIABLE NAME="%%SCRIPT_DIR" VALUE="/apps/etl"/>
    <JOB JOBNAME="PRXYZ1A001" TASKTYPE="Command" CMDLINE="%%SCRIPT_DIR/run.sh"/>
  </SMART_FOLDER>
</DEFTABLE>
"""

#: F2 — style: wrapped attributes, mixed indentation, single quotes, all three
#: empty-tag forms. The wrapped JOB is the case every DOM serializer destroys.
F2_STYLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ2B"
                DESCRIPTION="attributes wrapped across lines">
    <JOB JOBNAME="PRXYZ2B001" TASKTYPE="Command"
         NODEID="host-xyz-01" APPLICATION="XYZ"
\t RUN_AS='svc.xyz'
         CMDLINE="%%SCRIPT_DIR/run.sh -e prod"/>
    <JOB JOBNAME="PRXYZ2B002" TASKTYPE="Command" CMDLINE="a.sh" />
    <JOB JOBNAME="PRXYZ2B003" TASKTYPE="Command" CMDLINE="b.sh"></JOB>
  </SMART_FOLDER>
</DEFTABLE>
"""

#: F3 — residue: every element family the curated model does NOT carry, each
#: holding a %%reference so the rename post-conditions have something to catch.
F3_RESIDUE = b"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ3C">
    <VARIABLE NAME="%%SCRIPT_PATH" VALUE="/opt/dpl"/>
    <RULE_BASED_CALENDARS NAME="WORKDAYS" DAYS="ALL" DAYS_AND_OR="OR"/>
    <JOB JOBNAME="PRXYZ3C001" TASKTYPE="Command"
         DESCRIPTION="runs %%SCRIPT_PATH nightly"
         CMDLINE="%%SCRIPT_PATH/run.sh -env %%ENV"
         POSTCMD="cat %%SCRIPT_PATH/out.tok">
      <VARIABLE NAME="%%ENV" VALUE="prod"/>
      <INCOND NAME="PRXYZ3C000-OK" ODATE="ODAT" AND_OR="AND"/>
      <OUTCOND NAME="PRXYZ3C001-OK" ODATE="ODAT" SIGN="ADD"/>
      <QUANTITATIVE NAME="%%SCRIPT_PATH-pool" QUANT="1"/>
      <CONTROL NAME="CTL-%%ENV" TYPE="E"/>
      <ON STMT="*" CODE="NOTOK">
        <DOACTION ACTION="SET" WHAT="%%SCRIPT_PATH-flag"/>
        <DOMAIL DEST="ops-dl" SUBJECT="failed under %%SCRIPT_PATH"/>
      </ON>
      <CAPTURE PATTERN="rows=%%ENV" VAR="%%ROWS"/>
    </JOB>
    <SUB_FOLDER SUB_FOLDER_NAME="NESTED">
      <VARIABLE NAME="%%SCRIPT_PATH" VALUE="/opt/dpl/nested"/>
      <JOB JOBNAME="PRXYZ3C101" TASKTYPE="Command" CMDLINE="%%SCRIPT_PATH/clean.sh"/>
    </SUB_FOLDER>
  </SMART_FOLDER>
</DEFTABLE>
"""

#: F4 — entities: the five named refs, a literal '>', numeric char refs, CDATA,
#: and non-ASCII UTF-8 in a description.
F4_ENTITIES = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b"<DEFTABLE>\n"
    b'  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ4D"\n'
    b'                DESCRIPTION="caf\xc3\xa9 &amp; bar &lt;ETL&gt; &quot;quoted&quot; &apos;single&apos;">\n'
    b'    <JOB JOBNAME="PRXYZ4D001" TASKTYPE="Command"\n'
    b'         NOTE="gt > literal" TAB="a&#9;b" ALPHA="&#65;lpha" HEXA="&#x41;lpha"\n'
    b'         CMDLINE="run.sh --flag=&quot;x&quot;">\n'
    b"      <![CDATA[raw <text> stays put]]>\n"
    b"    </JOB>\n"
    b"  </SMART_FOLDER>\n"
    b"</DEFTABLE>\n"
)

#: F5 — prolog: single-quoted declaration, DOCTYPE with internal subset,
#: comments before and after the root, a PI, UTF-8 BOM, CRLF, no trailing newline.
F5_PROLOG = (
    b"\xef\xbb\xbf<?xml version='1.0' encoding='UTF-8'?>\r\n"
    b'<!DOCTYPE DEFTABLE SYSTEM "deftable.dtd" [\r\n'
    b"  <!ELEMENT DEFTABLE ANY>\r\n"
    b"]>\r\n"
    b"<!-- exported 2026-01-01 -->\r\n"
    b'<?ctm version="9.0.21.300"?>\r\n'
    b"<DEFTABLE>\r\n"
    b"  <!-- folder comment -->\r\n"
    b'  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ5E">\r\n'
    b'    <JOB JOBNAME="PRXYZ5E001" TASKTYPE="Command" CMDLINE="run.sh"/>\r\n'
    b"  </SMART_FOLDER>\r\n"
    b"</DEFTABLE>\r\n"
    b"<!-- trailing comment -->"
)

#: F6 — duplicates: the same variable name twice in one job, the same job name
#: twice in one folder, and a NAMELESS variable (position-faithfulness probe).
F6_DUPLICATES = b"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ6F">
    <JOB JOBNAME="PRXYZ6F001" TASKTYPE="Command" CMDLINE="one.sh">
      <VARIABLE NAME="%%DIR" VALUE="/first"/>
      <VARIABLE VALUE="orphan-value-no-name"/>
      <VARIABLE NAME="%%DIR" VALUE="/second"/>
    </JOB>
    <JOB JOBNAME="PRXYZ6F002" TASKTYPE="Command" CMDLINE="one.sh"/>
    <JOB JOBNAME="PRXYZ6F002" TASKTYPE="Command" CMDLINE="two.sh"/>
  </SMART_FOLDER>
</DEFTABLE>
"""

#: F7 — namespaces (defensive): xmlns on the root plus one prefixed element.
F7_NAMESPACES = b"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE xmlns:ctm="urn:example:ctm">
  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ7G">
    <ctm:EXTENSION KIND="vendor-private"/>
    <JOB JOBNAME="PRXYZ7G001" TASKTYPE="Command" CMDLINE="run.sh"/>
  </SMART_FOLDER>
</DEFTABLE>
"""

#: F8 — three levels of SUB_FOLDER nesting.
F8_NESTING = b"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ8H">
    <VARIABLE NAME="%%L0" VALUE="zero"/>
    <SUB_FOLDER SUB_FOLDER_NAME="A">
      <VARIABLE NAME="%%L1" VALUE="one"/>
      <SUB_FOLDER SUB_FOLDER_NAME="B">
        <VARIABLE NAME="%%L2" VALUE="two"/>
        <SUB_FOLDER SUB_FOLDER_NAME="C">
          <JOB JOBNAME="PRXYZ8H301" TASKTYPE="Command" CMDLINE="%%L0/%%L1/%%L2"/>
        </SUB_FOLDER>
      </SUB_FOLDER>
    </SUB_FOLDER>
  </SMART_FOLDER>
</DEFTABLE>
"""

#: F9 — ISO-8859-1 with a genuine high byte (0xE9, é) in a value.
F9_LATIN1 = (
    b'<?xml version="1.0" encoding="ISO-8859-1"?>\n'
    b"<DEFTABLE>\n"
    b'  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ9I" DESCRIPTION="caf\xe9">\n'
    b'    <JOB JOBNAME="PRXYZ9I001" TASKTYPE="Command" CMDLINE="run.sh"/>\n'
    b"  </SMART_FOLDER>\n"
    b"</DEFTABLE>\n"
)

#: F10 — UTF-16: must be REFUSED (byte-offset lexing is unsound there).
F10_UTF16 = (
    '<?xml version="1.0" encoding="UTF-16"?>\n'
    "<DEFTABLE>\n"
    '  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ0J"/>\n'
    "</DEFTABLE>\n"
).encode("utf-16")  # carries the LE BOM

#: F11 — the SAME folder name in TWO data centers: folder names are only
#: unique per DC, so identity without DATACENTER is half an identity.
F11_MULTI_DC = b"""<?xml version="1.0" encoding="UTF-8"?>
<DEFTABLE>
  <SMART_FOLDER DATACENTER="DC1" FOLDER_NAME="PRXYZ1A">
    <JOB JOBNAME="PRXYZ1A001" TASKTYPE="Command" CMDLINE="dc1.sh"/>
  </SMART_FOLDER>
  <SMART_FOLDER DATACENTER="DC2" FOLDER_NAME="PRXYZ1A">
    <JOB JOBNAME="PRXYZ1A001" TASKTYPE="Command" CMDLINE="dc2.sh"/>
  </SMART_FOLDER>
</DEFTABLE>
"""

#: The round-trip corpus: everything load_document must accept.
ROUND_TRIP_FIXTURES: dict[str, bytes] = {
    "F1_minimal": F1_MINIMAL,
    "F2_style": F2_STYLE,
    "F3_residue": F3_RESIDUE,
    "F4_entities": F4_ENTITIES,
    "F5_prolog": F5_PROLOG,
    "F6_duplicates": F6_DUPLICATES,
    "F7_namespaces": F7_NAMESPACES,
    "F8_nesting": F8_NESTING,
    "F9_latin1": F9_LATIN1,
    "F11_multi_dc": F11_MULTI_DC,
}
