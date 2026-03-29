"""Run the FastAPI server."""

import uvicorn

from stock_adviser.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("stock_adviser.server:app", host="0.0.0.0", port=8000, reload=True)
