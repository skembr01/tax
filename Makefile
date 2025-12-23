run:
	python3 run.py

venv:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

test:
	pytest -q

docker-run:
	gunicorn --bind 0.0.0.0:8000 run:app
