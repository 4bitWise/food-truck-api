FROM python:3
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
RUN ls
RUN cat app/main.py
CMD ["fastapi", "dev", "app/main.py"]