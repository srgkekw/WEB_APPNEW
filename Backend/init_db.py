﻿# Backend/init_db.py

from app import db, app

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✔ База данных была успешно инициализирована")
