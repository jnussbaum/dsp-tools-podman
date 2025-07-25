import os
import subprocess

import pyperf
from loguru import logger

# ruff: noqa:S607 (Starting a process with a partial executable path)


def teardown() -> None:
    logger.info("Entering teardown")
    subprocess.run(["dsp-tools", "stop-stack"], check=True)


def task_to_measure():
    logger.info("Starting task to measure")
    subprocess.run(["dsp-tools", "start-stack", "--no-prune"], check=True)


def main():
    os.environ["CONTAINER_ENGINE"] = "docker"
    logger.info("Container engine: docker")

    runner = pyperf.Runner(
        values=60,  # default = 3
        warmups=1,  # default = 1
        processes=1,  # default = 20
        loops=0,  # default = 0
        min_time=0.1,  # default = 0.1
        metadata=None,  # default = None
        show_name=True,  # default = True
        program_args=None,  # default = None
        add_cmdline_args=None,  # default = None
    )
    runner.timeit(
        name="start-stack",
        stmt="task_to_measure()",
        teardown="teardown()",
        globals=globals() | locals(),
    )


if __name__ == "__main__":
    main()
