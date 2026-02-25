#!/bin/bash
set -e

echo "==> [1/4] Installing system-level C build dependencies..."
sudo apt-get update -qq
sudo apt-get install -y \
  build-essential \
  cmake \
  libopenblas-dev \
  liblapack-dev \
  gfortran \
  libffi-dev \
  libssl-dev \
  curl

echo "==> [2/4] Installing Python backend dependencies..."
cd /workspaces/equant/backend
pip install --upgrade pip
pip install -r requirements.txt

echo "==> [3/4] Installing Node.js frontend dependencies..."
cd /workspaces/equant/frontend
npm install

echo "==> [4/4] Setup complete."
echo "  - Backend:  cd backend && uvicorn app.main:app --reload --port 8000"
echo "  - Frontend: cd frontend && npm run dev"
