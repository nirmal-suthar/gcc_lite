PYTHON=python3

all:
	mkdir -p ../bin
	$(PYTHON) -m pip install --ignore-installed -r ../requirements.txt
	$(PYTHON) -m py_compile lexer.py
	cp lexer.sh ../bin/lexer
	chmod +x ../bin/lexer

clean: 
	rm -rf ../bin/lexer ./__pycache__