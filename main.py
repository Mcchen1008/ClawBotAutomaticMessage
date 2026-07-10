from app.main import run_bot, run_web
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        run_web()
    else:
        run_bot()
