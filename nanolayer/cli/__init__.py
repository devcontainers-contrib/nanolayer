import logging
import os
import platform

import psutil
import sentry_sdk

from nanolayer.utils.linux_information_desk import EnvFile
from nanolayer.utils.settings import NanolayerSettings
from nanolayer.utils.version import resolve_own_package_version

logger = logging.getLogger(__name__)

try:
    dsn = NanolayerSettings().analytics_id if not NanolayerSettings().no_analytics else ""
    sentry_sdk.init(
        release=resolve_own_package_version(),
        traces_sample_rate=1.0,
        dsn=dsn,
        # explicitly turn off personally identifiable information
        send_default_pii=False,
        # explicitly turn off client reports
        send_client_reports=False,
        # explicitly turn off client reports
        request_bodies="never",
    )
    # explicitly strip any identifiable user information
    sentry_sdk.set_user(None)

    # ------ add only non-personally-identifiable hardware metrics -------
    sentry_sdk.set_context(
        "nanolayer.python",
        {
            # uname -a like
            "platform.uname": str(platform.uname()),
            # num of cores
            "os.cpu_count": os.cpu_count(),
            # 4GB 8GB 16GB etc
            "psutil.virtual_memory": str(psutil.virtual_memory()),
        },
    )
    os_release = EnvFile.parse("/etc/os-release")
    # x86_64 / ARM
    sentry_sdk.set_tag("nanolayer.arch", platform.machine())
    # ubuntu / debian / alpine / fedora etc
    sentry_sdk.set_tag("nanolayer.os_release.ID", os_release.get("ID", None))
    # debian for both ubuntu and debian, etc
    sentry_sdk.set_tag("nanolayer.os_release.ID_LIKE", os_release.get("ID_LIKE", None))
    # ubuntu 18.04 20.04 22.04 etc
    sentry_sdk.set_tag(
        "nanolayer.os_release.VERSION_ID", os_release.get("VERSION_ID", None)
    )
    # true if nanolayer is being used as a binary, false otherwise
    sentry_sdk.set_tag("nanolayer.binary_mode", "__file__" not in globals())

except Exception as e:  # no qa
    logger.warning("usage metrics are disabled")
