#!/bin/bash
echo "Установка зависимостей..."
python3 -m pip install -r requirements.txt
echo "Запуск Desktop-приложения MediaConverter Pro..."
python3 main.py
