runserver:
	python manage.py runserver 0.0.0.0:8000

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