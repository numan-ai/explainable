.PHONY: major minor patch

major:
	hatch version major
	hatch build
	hatch publish

minor:
	hatch version minor
	hatch build
	hatch publish

patch:
	hatch version patch
	hatch build
	hatch publish
