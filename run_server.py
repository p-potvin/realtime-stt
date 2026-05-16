import os
import sys
import logging
import json
import re
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import queue

# Setup basic logging with security-conscious defaults
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("run_server")

# NOTE: Before importing main_app, we need to setup a QApplication
# instance because it internally relies on PySide6 signals in module variables.
from PySide6.QtCore import QCoreApplication
q_app = QCoreApplication.instance()
if q_app is None:
    q_app = QCoreApplication(sys.argv)

from main_app import RealTimeSTTApp

app = FastAPI(title="Real-Time STT WebSocket/HTTP Server")
stt_app_instance = RealTimeSTTApp()

class CommandPayload(BaseModel):
    command: str

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/status")
async def get_status():
    return {"engine": stt_app_instance.active_engine}

@app.post("/command")
async def post_command(payload: CommandPayload):
    command = payload.command
    if not command or not isinstance(command, str) or not re.match(r"^[a-zA-Z0-9_-]+$", command):
        raise HTTPException(status_code=400, detail="Invalid command format")
    logger.info(f"Received valid command: {command}")
    return {"status": "success", "command": command}

# Store active websockets to broadcast to them
active_connections: list[WebSocket] = []
broadcast_queue = queue.Queue()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"Client connected to WebSocket: {websocket.client}")
    try:
        while True:
            data = await websocket.receive_text()
            safe_msg = data[:100]
            if safe_msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from WebSocket: {websocket.client}")
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)
        await websocket.close()

def broadcast_caption(text: str, label_idx: int):
    # Enqueue thread-safely
    logger.debug(f"Queueing caption for broadcast: '{text}'")
    broadcast_queue.put({"text": text, "label_idx": label_idx})

async def broadcast_loop():
    while True:
        # Exhaust the queue before sleeping to prevent burst backlogs
        while not broadcast_queue.empty():
            try:
                # Poll the queue non-blocking
                msg = broadcast_queue.get_nowait()
                if active_connections:
                    payload = json.dumps(msg)
                    tasks = [client.send_text(payload) for client in active_connections]
                    await asyncio.gather(*tasks, return_exceptions=True)
            except queue.Empty:
                break
        await asyncio.sleep(0.05)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_loop())

def main():
    HOST = '127.0.0.1'
    PORT = 8080

    logger.info("Initializing RealTime STT Application (Headless via uvicorn)...")

    # Hook into the caption update signal to broadcast via websockets
    stt_app_instance.bridge.update_caption_signal.connect(broadcast_caption)

    # Start the STT application processing
    stt_app_instance.start()

    # The uvicorn server runs the asyncio loop on the main thread
    try:
        uvicorn.run(app, host=HOST, port=PORT, log_level="info")
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
    finally:
        stt_app_instance.stop()

if __name__ == "__main__":
    main()
