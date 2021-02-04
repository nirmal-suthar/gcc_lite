PYTHON=python3

all:
	mkdir -p ../bin
	cp lexer.py ../bin/lexer
	$(PYTHON) -m py_compile ../bin/lexer
	chmod +x ../bin/lexer

clean: 
	rm -rf ../bin/lexer ../bin/__pycache__