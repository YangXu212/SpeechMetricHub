FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libsndfile1 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/speechmetrichub
COPY . .
RUN python -m pip install --no-cache-dir 'numpy<2' '.[transcription,quality,separation,diarization]'
ENTRYPOINT ["speechmetrichub"]
CMD ["list"]
