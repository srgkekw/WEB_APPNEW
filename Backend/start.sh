#!/bin/sh
python3 init_db.py &
python3 app.py &
python3 bot.py
