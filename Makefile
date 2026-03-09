SKILL_NAME := jetrehearing
ZIP_NAME := $(SKILL_NAME)-skill.zip

.PHONY: package clean install test release

package: clean
	mkdir -p $(SKILL_NAME)-skill
	cp -r skill/ install.py install.sh README.md VERSION $(SKILL_NAME)-skill/
	cd $(SKILL_NAME)-skill && rm -rf skill/.venv skill/node_modules skill/package-lock.json skill/__pycache__
	zip -r $(ZIP_NAME) $(SKILL_NAME)-skill/
	rm -rf $(SKILL_NAME)-skill

release: package
	@VERSION=$$(cat VERSION) && \
	git tag -a "v$$VERSION" -m "Release v$$VERSION" && \
	git push origin main && \
	git push origin "v$$VERSION" && \
	gh release create "v$$VERSION" $(ZIP_NAME) --title "v$$VERSION" --generate-notes && \
	echo "Released v$$VERSION"

clean:
	rm -f $(ZIP_NAME)

install:
	python3 install.py

test:
	@echo "Validating skill structure..."
	@test -f skill/SKILL.md || (echo "FAIL: skill/SKILL.md missing" && exit 1)
	@test -d skill/references || (echo "FAIL: skill/references/ missing" && exit 1)
	@test -d skill/scripts || (echo "FAIL: skill/scripts/ missing" && exit 1)
	@test -f skill/scripts/splitmarks.py || (echo "FAIL: skill/scripts/splitmarks.py missing" && exit 1)
	@test -f skill/scripts/extract_docx.py || (echo "FAIL: skill/scripts/extract_docx.py missing" && exit 1)
	@test -f skill/scripts/verify_citations.py || (echo "FAIL: skill/scripts/verify_citations.py missing" && exit 1)
	@test -f skill/references/rehearing-format.md || (echo "FAIL: skill/references/rehearing-format.md missing" && exit 1)
	@test -f skill/references/style-spec.md || (echo "FAIL: skill/references/style-spec.md missing" && exit 1)
	@test -f install.py || (echo "FAIL: install.py missing" && exit 1)
	@test -f README.md || (echo "FAIL: README.md missing" && exit 1)
	@test -f VERSION || (echo "FAIL: VERSION missing" && exit 1)
	@python3 -c "import py_compile; py_compile.compile('skill/scripts/extract_docx.py', doraise=True)"
	@python3 -c "import py_compile; py_compile.compile('skill/scripts/check_update.py', doraise=True)"
	@python3 -c "import py_compile; py_compile.compile('skill/scripts/verify_citations.py', doraise=True)"
	@python3 -c "import py_compile; py_compile.compile('skill/scripts/splitmarks.py', doraise=True)"
	@echo "All checks passed."
