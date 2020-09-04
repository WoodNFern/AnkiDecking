.PHONY:  init

init:
	(\
		git submodule init; \
		git submodule update; \
		[ -d "./venv" ] || python -m venv venv; \
		source venv/bin/activate; \
		pip install -r anki/pylib/requirements.dev; \
		pip install -r ./requirements.txt; \
	)