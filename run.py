import os
import subprocess
import sys
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

ROOT = Path(__file__).parent.resolve()

# Tu ma być KATALOG, który ZAWIERA pakiet `vetclinic_api`,
# a nie sam katalog pakietu.
API_ROOT = ROOT / "VetClinic" / "API"
GUI_DIR = ROOT / "VetClinic" / "GUI" / "vetclinic_gui"

procs: list[subprocess.Popen] = []


def start_processes() -> None:
    """Uruchom API i GUI z poprawnym PYTHONPATH-em."""
    global procs
    stop_processes()
    print("🚀 Uruchamiam API i GUI…")

    env = os.environ.copy()
    # Czyścimy stare PYTHONPATH, które może wskazywać na stare repo
    env.pop("PYTHONPATH", None)
    # Ustawiamy PYTHONPATH tak, żeby Python widział TĘ wersję vetclinic_api
    env["PYTHONPATH"] = str(API_ROOT)

    procs = [
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "vetclinic_api.main:app", "--reload"],
            cwd=str(API_ROOT),
            env=env,
        ),
        subprocess.Popen(
            [sys.executable, "-m", "vetclinic_gui.main"],
            cwd=str(GUI_DIR),
            env=env,
        ),
    ]


def stop_processes() -> None:
    global procs
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(0.5)
    procs = []


def on_change(event) -> None:
    print(f"🔄 Detected change in {event.src_path!r}, restarting…")
    start_processes()


if __name__ == "__main__":
    start_processes()

    handler = PatternMatchingEventHandler(
        patterns=["*.py"],
        ignore_directories=True,
    )
    handler.on_modified = on_change
    handler.on_created = on_change
    handler.on_deleted = on_change

    observer = Observer()
    observer.schedule(handler, str(API_ROOT), recursive=True)
    observer.schedule(handler, str(GUI_DIR), recursive=True)
    observer.start()

    print("👀 Watching for changes. Ctrl+C to quit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🏁 Stopping…")
        observer.stop()

    observer.join()
    stop_processes()
