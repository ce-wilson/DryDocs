"""Parse Control-M folder names into structured properties.

Naming convention (per the production support team's spec):

    <PREFIX>-<SEGMENT>-<SEGMENT>-...-<SUFFIX>

The first segment (no dashes) carries the environment + LOB + appcode +
folder-type signature in positions:

    Position 1     environment        P=Production, D=Dev, Q=QA
    Position 2     LOB code           R=Retail
    Positions 3-5  appcode (3-char)   e.g. ARA, DAT, SRV
    Position 6     folder type        G=Smart folder,D=Daily, M=Monthly, etc.

Example:  ``PRARAG-HLDM-111027-PEX-RFND-DLY``
    P    -> Production
    R    -> Retail
    ARA  -> appcode
    G    -> Smart folder
    HLDM, 111027, PEX, RFND, DLY  -> Folder domain segments

Some teams use the ``APPLICATION`` column on ``CM_DEF_VJOB`` to carry a
3-char appcode, others use it for a Platform name. **It does NOT
reliably reconcile to a SEAL appcode.** The folder-name appcode (this
module) is the canonical mechanism for tying folders to applications,
mediated by a small appcode-to-SEAL crosswalk that lives outside this
module (M3 phase / M4 deliverable).
"""
from __future__ import annotations

from dataclasses import dataclass

ENVIRONMENT_MAP = {
    "P": "Production",
    "D": "Development",
    "Q": "QA",
}

LOB_CODE_MAP = {
    "R": "Retail",
    "Y": "Credit Cards"  # provisional
    }

FOLDER_TYPE_MAP = {
    "G": "Smart folder",
    "D": "Daily",
    "M": "Monthly",
    "R": "Ad-hoc"  # provisional
}


@dataclass(frozen=True)
class ParsedFolderName:
    """Structured view of a parsed Control-M folder name.

    ``prefix_recognized`` is True iff the first segment is at least 6
    characters long and ends in a recognised folder-type letter or has
    a usable appcode. Use this to decide whether the structured fields
    can be trusted; otherwise treat as opaque.
    """

    raw: str
    prefix: str                  # the first segment (e.g. "PRARAG")
    environment_code: str | None # 'P'
    environment: str | None      # 'Production'
    lob_code: str | None         # 'R'
    lob: str | None              # 'Retail'
    app_code: str | None         # 'ARA'
    folder_type_code: str | None # 'G'
    folder_type: str | None      # 'Smart folder'
    segments: tuple[str, ...]    # the segments AFTER the prefix
    prefix_recognized: bool


def parse_folder_name(name: str) -> ParsedFolderName:
    """Parse a folder name. Always returns a result; check ``prefix_recognized``."""
    raw = (name or "").strip()
    if "-" in raw:
        prefix, _, rest = raw.partition("-")
        segments = tuple(rest.split("-"))
    else:
        prefix = raw
        segments = ()

    env_code: str | None = None
    env: str | None = None
    lob_code: str | None = None
    lob: str | None = None
    app_code: str | None = None
    ftype_code: str | None = None
    ftype: str | None = None
    recognized = False

    if len(prefix) >= 6:
        ec = prefix[0:1].upper()
        lc = prefix[1:2].upper()
        ac = prefix[2:5].upper()
        fc = prefix[5:6].upper()
        if ec in ENVIRONMENT_MAP:
            env_code = ec
            env = ENVIRONMENT_MAP[ec]
            recognized = True
        if lc in LOB_CODE_MAP:
            lob_code = lc
            lob = LOB_CODE_MAP[lc]
        if ac.isalpha():
            app_code = ac
        if fc in FOLDER_TYPE_MAP:
            ftype_code = fc
            ftype = FOLDER_TYPE_MAP[fc]
        elif fc:
            ftype_code = fc
            ftype = None  # unknown type letter

    return ParsedFolderName(
        raw=raw,
        prefix=prefix,
        environment_code=env_code,
        environment=env,
        lob_code=lob_code,
        lob=lob,
        app_code=app_code,
        folder_type_code=ftype_code,
        folder_type=ftype,
        segments=segments,
        prefix_recognized=recognized,
    )
