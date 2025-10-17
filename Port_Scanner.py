#!/usr/bin/env python3
"""
Port scanner semplice (didattico).
Usalo solo su host di cui hai il permesso (es. localhost, VM, lab).
"""

import socket
import threading
import argparse
from queue import Queue
import time

# ---------- Parametri di default ----------
DEFAULT_TIMEOUT = 1.0    # secondi per tentativo di connessione
DEFAULT_THREADS = 100    # numero max di thread concorrenti
# ------------------------------------------

def scan_port(host: str, port: int, timeout: float) -> bool:
    """Ritorna True se la porta è aperta (connect succeeds), False altrimenti."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

def worker(host: str, timeout: float, q: Queue, open_ports: list, lock: threading.Lock):
    """Worker thread che prende porte dalla coda e le scansiona."""
    while True:
        try:
            port = q.get_nowait()
        except Exception:
            return
        is_open = scan_port(host, port, timeout)
        if is_open:
            with lock:
                open_ports.append(port)
                print(f"[OPEN] {host}:{port}")
        q.task_done()

def run_scan(host: str, start_port: int, end_port: int, timeout: float, threads: int):
    q = Queue()
    for port in range(start_port, end_port + 1):
        q.put(port)

    open_ports = []
    lock = threading.Lock()
    thread_list = []

    start_time = time.time()
    for _ in range(min(threads, q.qsize())):
        t = threading.Thread(target=worker, args=(host, timeout, q, open_ports, lock), daemon=True)
        t.start()
        thread_list.append(t)

    # attendi che la coda sia vuota
    q.join()
    elapsed = time.time() - start_time

    open_ports.sort()
    print("\n--- Risultato scansione ---")
    print(f"Host: {host}")
    print(f"Porte {start_port} - {end_port}")
    print(f"Porte aperte: {open_ports if open_ports else 'Nessuna'}")
    print(f"Tempo impiegato: {elapsed:.2f} s")

def parse_args():
    p = argparse.ArgumentParser(description="Port scanner TCP semplice (didattico).")
    p.add_argument("host", help="Host da scansionare (nome o IP).")
    p.add_argument("-s", "--start", type=int, default=1, help="Porta iniziale (default 1).")
    p.add_argument("-e", "--end", type=int, default=1024, help="Porta finale (default 1024).")
    p.add_argument("-t", "--threads", type=int, default=DEFAULT_THREADS, help=f"Numero di thread concorrenti (default {DEFAULT_THREADS}).")
    p.add_argument("-T", "--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"Timeout in secondi per tentativo (default {DEFAULT_TIMEOUT}).")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # Validazioni semplici
    if args.start < 1 or args.end > 65535 or args.start > args.end:
        print("Intervallo porte non valido. Usa valori tra 1 e 65535 e assicurati start <= end.")
        raise SystemExit(1)

    print(f"Avvio scansione su {args.host} porte {args.start}-{args.end} con {args.threads} thread, timeout {args.timeout}s")
    run_scan(args.host, args.start, args.end, args.timeout, args.threads)
