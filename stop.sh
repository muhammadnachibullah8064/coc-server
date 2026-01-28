#!/bin/bash

pkill -f "uvicorn server:app"
pkill cloudflared