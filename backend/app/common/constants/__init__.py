"""Every threshold and limit used by the backend (constitution Principle XIV).

Change a value in the area module, not in the code that uses it. Import from `app.common.constants`.
Children: core (001), leakage (002), chat (003), llm (003 providers), fira (004), report (005).
"""

from app.common.constants.chat import *  # noqa: F403 - this package is the single entry point
from app.common.constants.core import *  # noqa: F403
from app.common.constants.fira import *  # noqa: F403
from app.common.constants.leakage import *  # noqa: F403
from app.common.constants.llm import *  # noqa: F403
from app.common.constants.report import *  # noqa: F403
