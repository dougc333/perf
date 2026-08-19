#!/bin/sh

curl -LsSf https://astral.sh/uv/install.sh | sh

uv venv venv
source venv/bin/activate