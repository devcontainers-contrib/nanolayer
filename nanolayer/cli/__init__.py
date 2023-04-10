import logging
import os
import platform

import sentry_sdk

from nanolayer.utils.linux_information_desk import EnvFile, ProcFile
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
    os_release_file = EnvFile.parse("/etc/os-release")
    meminfo_file =  ProcFile.parse("/proc/meminfo")

    sentry_sdk.set_context(
        "nanolayer",
        {
            # uname -a like
            "uname": str(platform.uname()),
            # num of cores
            "python.os.cpu_count": os.cpu_count(),
            # 4GB 8GB 16GB etc
            "fs.proc.meminfo.MemTotal": meminfo_file['MemTotal'],
            # 4GB 8GB etc
            "fs.proc.meminfo.MemFree": meminfo_file['MemFree'],
        },
    )
 
    # x86_64 / ARM
    sentry_sdk.set_tag("nanolayer.python.platform.machine", platform.machine())
    # ubuntu / debian / alpine / fedora etc
    sentry_sdk.set_tag("nanolayer.fs.etc.os-release.ID", os_release_file.get("ID", None))
    # debian for both ubuntu and debian, etc
    sentry_sdk.set_tag("nanolayer.fs.etc.os-release.ID_LIKE", os_release_file.get("ID_LIKE", None))
    # ubuntu 18.04 20.04 22.04 etc
    sentry_sdk.set_tag(
        "nanolayer.fs.etc.os-release.VERSION_ID", os_release_file.get("VERSION_ID", None)
    )
    # true if nanolayer is being used as a binary, false otherwise
    sentry_sdk.set_tag("nanolayer.binary_mode", "__file__" not in globals())

except Exception as e:  # no qa
    logger.warning("usage metrics are disabled")
