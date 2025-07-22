import os
import platform
import subprocess
import warnings

import pyperf
from loguru import logger

# ruff: noqa:S607 (Starting a process with a partial executable path)


def clear_mac_system_caches() -> None:
    """Sync filesystem with 'sync' and clear system caches using 'purge'"""
    logger.info("Clearing Mac system caches")
    subprocess.run(["sync"], check=False)
    subprocess.run(["purge"], check=False)


def clear_linux_system_caches() -> None:
    """Sync filesystem with 'sync' and clear system caches using 'echo 3 > /proc/sys/vm/drop_caches'"""
    logger.info("Clearing Linux system caches")
    subprocess.run(["sync"], check=False)
    subprocess.run(["sudo", "sh", "-c", "sync && echo 3 > /proc/sys/vm/drop_caches"], check=False)


def setup() -> None:
    logger.info("Entering setup")
    if platform.system() == "Darwin":
        pass
        # clear_mac_system_caches() only works for docker
    elif platform.system() == "Linux":
        clear_linux_system_caches()
    else:
        warnings.warn(f"{platform.system()=}")
    logger.info("Run 'dsp-tools start-stack'...")
    subprocess.run(["dsp-tools", "start-stack", "--no-prune"], check=True)


def teardown() -> None:
    logger.info("Entering teardown")
    subprocess.run(["dsp-tools", "stop-stack"], check=True)


def task_to_measure():
    logger.info("Starting task to measure")
    subprocess.run(["dsp-tools", "create", "testdata/json-project/test-project-systematic.json"], check=True)
    subprocess.run(["dsp-tools", "xmlupload", "testdata/xml-data/test-data-systematic.xml"], check=True)


def main():
    os.environ["CONTAINER_ENGINE"] = "docker"
    logger.info("Container engine: docker")

    runner = pyperf.Runner(
        values=3,  # default = 3
        warmups=1,  # default = 1
        processes=4,  # default = 20
        loops=0,  # default = 0
        min_time=0.1,  # default = 0.1
        metadata=None,  # default = None
        show_name=True,  # default = True
        program_args=None,  # default = None
        add_cmdline_args=None,  # default = None
    )
    runner.timeit(
        name="xmlupload",
        stmt="task_to_measure()",
        setup="setup()",
        teardown="teardown()",
        globals=globals() | locals(),
    )


if __name__ == "__main__":
    main()
