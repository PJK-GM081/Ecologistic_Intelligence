import argparse
import os
import sys
from pathlib import Path

import uvicorn

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Run API server."""
    parser = argparse.ArgumentParser(description="Ecologistic Intelligence API Server")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Port to run on",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("API_HOST", "127.0.0.1"),
        help="Host to bind to",
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode with multiple workers",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("API_WORKERS", "4")),
        help="Number of worker processes in production mode",
    )

    args = parser.parse_args()

    if args.prod:
        print("Starting API server in PRODUCTION mode")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Workers: {args.workers}")
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level="info",
        )
        return

    print("Starting API server in DEVELOPMENT mode")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print("Auto-reload: enabled")
    print(f"Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"ReDoc: http://{args.host}:{args.port}/redoc")
    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    main()

