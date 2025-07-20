import os
import subprocess
from typing import Literal

import pyperf

# ruff: noqa:S607 (Starting a process with a partial executable path)


def clear_mac_system_caches() -> None:
    """Sync filesystem with 'sync' and clear system caches using 'purge'"""
    subprocess.run(["sync"], check=False)
    subprocess.run(["purge"], check=False)
    'sudo sh -c "sync && echo 3 > /proc/sys/vm/drop_caches"'


def setup() -> None:
    clear_mac_system_caches()
    subprocess.run(["dsp-tools", "start-stack", "--no-prune"], check=True)


def teardown() -> None:
    subprocess.run(["dsp-tools", "stop-stack"], check=True)


def task_to_measure():
    subprocess.run(["dsp-tools", "create", "testdata/json-project/test-project-systematic.json"], check=True)
    subprocess.run(["dsp-tools", "xmlupload", "testdata/xml-data/test-data-systematic.xml"], check=True)


def main():
    container_engine: Literal["podman", "docker"] = "docker"
    os.environ["CONTAINER_ENGINE"] = container_engine

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
        name="run start-stack",
        stmt="task_to_measure()",
        setup="setup()",
        teardown="teardown()",
        globals=globals() | locals(),
    )


if __name__ == "__main__":
    main()
