import subprocess, sys, signal, time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

ROOT    = Path(__file__).parent.resolve()
API_DIR = ROOT / "VetClinic" / "API" / "vetclinic_api"
GUI_DIR = ROOT / "VetClinic" / "GUI" / "vetclinic_gui" 

procs = []

def start_processes():
    global procs
    stop_processes()
    print("🚀 Uruchamiam API i GUI…")
    procs = [
        subprocess.Popen(
            ["uvicorn", "vetclinic_api.main:app"], 
            cwd=str(API_DIR)
        ),
        subprocess.Popen(
            [sys.executable, "-m", "vetclinic_gui.main"],
            cwd=str(GUI_DIR)
        )
    ]

def stop_processes():
    global procs
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(0.5)
    procs = []

def on_change(event):
    print(f"🔄 Detected change in {event.src_path!r}, restarting…")
    start_processes()

if __name__ == "__main__":
    start_processes()

    handler = PatternMatchingEventHandler(patterns=["*.py"], ignore_directories=True)
    handler.on_modified = on_change
    handler.on_created  = on_change
    handler.on_deleted  = on_change

    observer = Observer()
    observer.schedule(handler, str(API_DIR), recursive=True)
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
