#!/usr/bin/env python3
"""Minimal SSE test to verify streaming works."""
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def simple_generator():
    """Simple working SSE generator."""
    for i in range(5):
        data = f'{{"count": {i}}}'
        yield f"data: {data}\n\n".encode('utf-8')
        await asyncio.sleep(1)

@app.get("/test-sse")
async def test_sse():
    return StreamingResponse(
        simple_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
