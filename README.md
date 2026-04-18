# FastAPI Worker System

A production-style starter project that demonstrates how to handle CPU-bound background jobs in FastAPI without blocking API responsiveness.

## Problem

FastAPI endpoints should respond quickly, but CPU-heavy work can block request handling if executed directly inside the API process.

## Solution

This project submits CPU-bound jobs to a separate process using `ProcessPoolExecutor`, then tracks progress with task IDs and a status endpoint.

## Architecture

Client -> FastAPI API -> ProcessPoolExecutor Worker -> In-memory Task Registry

## Endpoints

### `POST /scan`

Start a CPU-heavy scan.

Request:
```json
{
  "number": 500000
}
