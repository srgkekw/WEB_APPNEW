#!/bin/sh
echo 
python3 init_db.py

echo 
python3 app.py &

echo 
python3 bot.py


