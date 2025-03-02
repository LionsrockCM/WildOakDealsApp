
.PHONY: test test-all create-test install-deps

test:
	python run_tests.py --run $(MODULE)

test-all:
	python run_tests.py --all

create-test:
	python run_tests.py --create $(MODULE) --test-funcs $(FUNCS)

install-deps:
	pip install -r requirements.txt
