#!/bin/bash
if ! [[ -d venv ]]; then
    echo "Missing venv, setting up python"
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Venv found"
fi
