DEVELOPER_DIR ?= /Users/raahil/Downloads/Xcode.app/Contents/Developer
XCODEBUILD = DEVELOPER_DIR=$(DEVELOPER_DIR) xcodebuild

.PHONY: install test lint check run api-dev format xcode-list simulator-build model-check model-smoke

install:
	python3 -m pip install -e 'backend[dev]'

test:
	.venv/bin/python -m pytest backend/tests -q

lint:
	.venv/bin/ruff check backend inference

check: lint test xcode-list

api-dev:
	.venv/bin/python -m uvicorn app.main:app --app-dir backend

run:
	$(MAKE) api-dev

format:
	.venv/bin/ruff check backend inference --fix

model-check:
	.venv/bin/python -c "from pathlib import Path; p=Path('inference/model_adapter.py'); print('adapter:', p, 'exists=', p.exists()); print('REAL_MODEL must fail if checkpoint is unavailable')"

model-smoke:
	@echo 'Requires an authorized real video fixture and configured GPU/model cache; no synthetic fallback is run.'

xcode-list:
	$(XCODEBUILD) -list -project ios/VoiceBack.xcodeproj

simulator-build:
	$(XCODEBUILD) -project ios/VoiceBack.xcodeproj -scheme VoiceBack \
		-sdk iphonesimulator -configuration Debug \
		-derivedDataPath /tmp/VoiceBackDerived CODE_SIGNING_ALLOWED=NO build

