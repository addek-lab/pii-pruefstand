import sys

from .cli import main

if __name__ == "__main__":
    # Windows-Konsolen nutzen oft eine alte Codepage; Umlaute sollen trotzdem sauber ausgegeben werden.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
