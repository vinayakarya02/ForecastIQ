.PHONY: help install etl analytics forecast pipeline app test lint format check

help:  ## Show this help
	@echo "ForecastIQ - common tasks"
	@echo "  make install    install package + app/dev extras"
	@echo "  make etl        build the warehouse from the dataset"
	@echo "  make analytics  run the analytics pipeline"
	@echo "  make forecast   run the forecasting pipeline"
	@echo "  make pipeline   etl + analytics + forecast"
	@echo "  make app        launch the Streamlit app"
	@echo "  make test       run the test suite"
	@echo "  make lint       ruff lint"
	@echo "  make format     ruff format"
	@echo "  make check      lint + format check + tests"

install:
	pip install -e ".[app,dev]"

etl:
	python pipelines/run_etl.py

analytics:
	python pipelines/run_analytics.py

forecast:
	python pipelines/run_forecast.py

pipeline: etl analytics forecast

app:
	streamlit run app/app.py

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

check:
	ruff check . && ruff format --check . && pytest -q
