#
#  Makefile
#

.PHONY: help serve view poll

help:
	@echo 'Available commands:'
	@echo
	@echo '  make env     Install required packages.'
	@echo '  make serve   Run the development server.'
	@echo '  make view    Open a browser to the developement URI.'
	@echo '  make poll    Run checks just once.'
	@echo '  make watch   Run checks every time the checks file changes.'
	@echo

env:
	test -d env || pyvenv env
	env/bin/pip install -r requirements.txt

db.yml:
	@echo 'Please configure db.yml with your database settings.'
	exit 1

checks.yml:
	@echo 'Please configure checks.yml with your constraints.'
	exit 1

poll: poll.py db.yml checks.yml
	env/bin/python $< db.yml checks.yml output.json

serve: checks.yml
	env/bin/python serve.py checks.yml output.json

watch: env/bin/watchmedo
	env/bin/watchmedo shell-command -c 'clear; make poll' --pattern='checks.yml' -wWR .

env/bin/watchmedo:
	env/bin/pip install watchdog

view:
	open http://127.0.0.1:5000/
