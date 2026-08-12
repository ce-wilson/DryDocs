"""Control-M definition-XML tag/attribute vocabulary — the shared synonym tables.

WHY THIS LIVES IN CORE. Two components read Control-M definition XML for
different jobs: the lineage extractor stages a curated projection for the
graph loaders, and the remediation ``xml_io`` locates byte spans for the
minimal-diff fix emitter. Components never import each other
(``tests/unit/test_module_boundary.py``), so the tag-name and
attribute-synonym VOCABULARY — which container tags exist, which attribute
spellings carry the description, which post-command typo the environment
actually contains — must live at the one level both may import. This is
shared vocabulary, not a shared parser: the same reasoning that keeps one
variable resolver keeps one synonym table, because two drifting copies of
"POSCMD is a real observed spelling" is how one side silently stops seeing
a field the other side still edits.

The spellings themselves are GROUNDED in the 9.0.21.300 export shape as
observed through the sanitized samples and the vendor corpus
(``external/orchestration/bmc-controlm/``); the authoritative element schema
(the EM ``.dtd`` files) is still a known acquisition gap, so these tables
record what has been SEEN, not what the DTD promises. New synonyms are
appended, never substituted, so both consumers widen together.
"""

from __future__ import annotations

#: folder-level container tags (newer / older format synonyms)
FOLDER_TAGS = frozenset({"FOLDER", "SMART_FOLDER", "TABLE", "SMART_TABLE"})
SMART_TAGS = frozenset({"SMART_FOLDER", "SMART_TABLE"})
SUBFOLDER_TAGS = frozenset({"SUB_FOLDER", "SUBFOLDER"})

#: attribute synonyms, first hit wins
FOLDER_NAME_ATTRS = ("FOLDER_NAME", "TABLE_NAME")
SUBFOLDER_NAME_ATTRS = ("SUB_FOLDER_NAME", "FOLDER_NAME", "JOBNAME")
DESCRIPTION_ATTRS = ("DESCRIPTION", "DESC")
#: post-execution command — the observed spellings, POSCMD typo included
POSTCMD_ATTRS = ("POSTCMD", "POST_CMD", "POSTCOMMAND", "POSCMD")
#: FileWatcher watched-path template
WATCH_ATTRS = ("FILE_PATH", "WATCH_FILE")

#: the notification family REQ-2 governs — recorded by name, not just counted
NOTIFICATION_TAGS = frozenset({"SHOUT", "DOSHOUT", "DOMAIL"})
#: scanning for those stops at a nested job/sub-folder: their notifications
#: belong to THEM, not to the container
SCAN_STOP_TAGS = SUBFOLDER_TAGS | {"JOB"}
