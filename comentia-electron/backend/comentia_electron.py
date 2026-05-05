import sys
import json
import time

def emit(event, **data):
    print(json.dumps({"event": event, **data}), flush=True)

def main():
    if len(sys.argv) < 2:
        emit("error", message="Falta URL")
        return

    url = sys.argv[1]
    total = 10

    emit("start", total=total, url=url)

    for i in range(1, total + 1):
        time.sleep(0.4)  # Simulación de trabajo
        emit("progress", current=i, total=total, percent=int(i / total * 100))

    emit("done", message="Descarga completada")

if __name__ == "__main__":
    main()