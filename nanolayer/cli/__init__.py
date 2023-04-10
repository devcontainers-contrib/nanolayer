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
            "cpu_count": os.cpu_count(),
            # 4GB 8GB 16GB etc
            "total_memory": meminfo_file['MemTotal'],
            # 4GB 8GB etc
            "free_memory": meminfo_file['MemFree'],
        },
    )
 
    # architecture such as x86_64, ARM etc
    sentry_sdk.set_tag("architecture", platform.machine())
    # distro id,  eg ubuntu / debian / alpine / fedora
    sentry_sdk.set_tag("os_release_id", os_release_file.get("ID", None))
    # distro id category, for example "debian" for both debian and ubuntu
    sentry_sdk.set_tag("os_release_id_like", os_release_file.get("ID_LIKE", None))
    # distro version, for example for ubuntu it will be 18.04 20.04 22.04 etc
    sentry_sdk.set_tag(
        "os_release_version_id", os_release_file.get("VERSION_ID", None)
    )
    # boolean - true if nanolayer is being used as a binary, false if used as a python package
    sentry_sdk.set_tag("nanolayer.binary_mode", "__file__" not in globals())

except Exception as e:  # no qa
    logger.warning("usage metrics are disabled")
