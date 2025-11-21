#!/bin/bash
uvicorn src.polyseek_sentient.main:app --host 0.0.0.0 --port ${PORT:-8000}
