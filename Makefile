.PHONY: major minor patch

major:
	rm -rf dist/
	hatch version major
	hatch build
	hatch publish

minor:
	rm -rf dist/
	hatch version minor
	hatch build
	hatch publish

patch:
	rm -rf dist/
	hatch version patch
	hatch build
	hatch publish
