#!/usr/bin/env python3
import subprocess
import time
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANAGE_PY = os.path.join(BASE_DIR, "manage.py")
PYTHON = os.environ.get("PYTHON_EXECUTABLE", "python")


def run_command():
    try:
        subprocess.run(
            [PYTHON, MANAGE_PY, "notificar_sla_vencido"],
            check=True,
        )
    except subprocess.CalledProcessError:
        pass


if __name__ == "__main__":
    while True:
        run_command()
        time.sleep(300)
