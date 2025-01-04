# Použijeme oficiální Python image jako základ
FROM python:3.9-slim

# Nastavíme pracovní adresář v kontejneru
WORKDIR /app

# Zkopírujeme requirements a nainstalujeme závislosti
COPY requirements.txt /app/
RUN echo "Instalujeme závislosti z requirements.txt"
RUN pip install -r requirements.txt
RUN echo "Závislosti nainstalovány"

# Zkopírujeme skripty do /app
RUN echo "Kopírujeme skripty do pracovního adresáře"
COPY python_stuff/ /app/

# Spustíme obě Dash aplikace na různých portech
RUN echo "Spouštíme aplikace na různých portech"
CMD python chat-test.py --port=$DASH_CHAT_PORT & \
    python main.py --port=$DASH_MAIN_PORT
