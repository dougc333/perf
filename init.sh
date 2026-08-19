#!/usr/bin/env bash


# 1. Install the venv package
apt update && apt install python3-venv -y

# 2. Create a virtual environment
python3 -m venv ~/myenv

# 3. Activate it
source ~/myenv/bin/activate

# 4. Now install transformers (your prompt will change to show the venv is active)
pip install transformers torch