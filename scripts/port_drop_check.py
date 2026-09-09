"""port_drop_check.py — every path a port apply REMOVED since a ref, against the
side-local ``accepted_drops:`` rulings (PORT4).

Run from the consumer apply tree, with the pre-port tag as the ref::

    poetry run python scripts/port_drop_check.py port-base-20260908

Exit 0 when every drop is ruled and no ruling is stale; 1 when an unruled drop or a
stale ruling is found; 2 when the ref or the manifest could not be read. A ruled drop
is LISTED, never silenced. The logic lives in ``drydocs.port.port_drops``; this file is
the entry point only.
"""

import sys

from drydocs.port.port_drops import main

if __name__ == "__main__":
    sys.exit(main())
