FROM python:3.12-slim

WORKDIR /app

# Optional but recommended: makes FKF_RUN_TIME line up with your local clock
ENV TZ=Europe/Budapest

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fkf.py email_utils.py scheduler.py ./

# Run as non-root
RUN useradd --create-home appuser
USER appuser

CMD ["python", "scheduler.py"]
