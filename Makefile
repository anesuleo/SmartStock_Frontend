APP = app.main:app
PID_FILE = .uvicorn.pid

install:
	pip install -r requirements.txt
run:
	python -m app.main

