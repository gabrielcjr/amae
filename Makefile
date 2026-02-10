runserver:
	python manage.py runserver 0.0.0.0:8000

runserver-80:
	sudo /home/ubuntu/amae/.venv/bin/python manage.py runserver 0.0.0.0:80

runserver-prod:
	sudo /home/ubuntu/amae/.venv/bin/gunicorn --bind 0.0.0.0:80 --workers 4 amae.wsgi:application

stop-prod:
	sudo pkill -f "gunicorn.*amae.wsgi"

.PHONY: seeds
seeds:
	@echo "Deseja rodar o comando seed? Ao executá-lo, o banco de dados será limpo e as tabelas e fixtures recriadas (s/N)."; \
	read -p "Resposta: " answer; \
	if [ "$$answer" = "s" ]; then \
		python manage.py seed --refresh; \
	else \
		echo "Cancelado"; \
	fi

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

startapp:
	python manage.py startapp $(name)

add-pkg:
	@read -p "Enter package name: " pkg; \
	pip install $$pkg && pip freeze > requirements.txt

pip-install:
	pip install -r requirements.txt

collectstatic:
	python manage.py collectstatic

watch-assets:
	npm run dev:css

reload-assets:
	rm -rf .assets
	rm -rf static
	mkdir .assets
	python manage.py collectstatic

run-check-flake8:
	flake8 . --config .flake8 --count --show-source --statistics

run-check-black:
	black --check . --config pyproject.toml

run-fix-black:
	black . --config pyproject.toml

run-check-isort:
	isort . --check-only --settings-file pyproject.toml

run-fix-isort:
	isort . --settings-file pyproject.toml

run-fix-autoflake:
	autoflake --remove-all-unused-imports --recursive --in-place . --exclude=apps.py,.venv

run-check-linters:
	make run-check-flake8
	make run-check-black
	make run-check-isort

run-fix-linters:
	make run-fix-black
	make run-fix-isort
	make run-fix-autoflake