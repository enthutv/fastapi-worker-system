## Frontend UI
https://github.com/enthutv/fastapi-worker-ui

# FastAPI Worker System

A distributed background job processing system with real-time monitoring.

---

## Overview

This system demonstrates how to handle CPU-intensive workloads without blocking the main application by offloading execution to distributed workers.

It combines FastAPI, Celery, Redis, and WebSockets to provide a scalable and responsive architecture.

---

## Tech Stack

- FastAPI (API layer)
- Celery (distributed workers)
- Redis (message broker)
- WebSocket (real-time updates)

---

## Features

- Asynchronous background task execution
- Real-time task status updates via WebSocket
- Live logs streaming
- Task history tracking
- CPU workload simulation

---

## Architecture

Frontend (Next.js)  
⬇  
FastAPI (API)  
⬇  
Celery Workers  
⬇  
Redis Queue  

---

## Run Locally

### Backend
```bash
uvicorn app.main:app --reload
