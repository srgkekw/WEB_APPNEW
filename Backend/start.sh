#!/bin/sh
python init_db.py &
python app.py &
python bot.py
