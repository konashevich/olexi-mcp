import os
import uvicorn


def main() -> None:
    # Cloud Run defaults PORT to 8080
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
