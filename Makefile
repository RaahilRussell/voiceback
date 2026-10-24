DEVELOPER_DIR ?= /Users/raahil/Downloads/Xcode.app/Contents/Developer
XCODEBUILD = DEVELOPER_DIR=$(DEVELOPER_DIR) xcodebuild

.PHONY: install test run format xcode-list simulator-build

install:
	python3 -m pip install -e 'backend[dev]'

test:
	python3 -m pytest backend/tests

run:
	python3 -m uvicorn app.main:app --app-dir backend --reload

format:
	python3 -m ruff check backend inference --fix

xcode-list:
	$(XCODEBUILD) -list -project ios/VoiceBack.xcodeproj

simulator-build:
	$(XCODEBUILD) -project ios/VoiceBack.xcodeproj -scheme VoiceBack \
		-sdk iphonesimulator -configuration Debug \
		-derivedDataPath /tmp/VoiceBackDerived CODE_SIGNING_ALLOWED=NO build

