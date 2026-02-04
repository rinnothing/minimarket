.PHONY: migrate
migrate:
	alembic upgrade head

.PHONY: remigrate
remigrate:
	alembic downgrade base
	alembic upgrade head
