SHELL=/usr/bin/bash
PYTHON=python3
SRC=./src
BIN=./bin

all: 
	mkdir -p $(BIN)
	$(PYTHON) -m py_compile $(SRC)/lexer.py $(SRC)/parser.py
	$(PYTHON) $(SRC)/parser.py

	ln -sf $(PWD)/$(SRC)/gcc_lite.py $(BIN)/gcc_lite
	chmod u+x $(BIN)/gcc_lite
	
dep:
	$(PYTHON) -m pip install --ignore-installed -r ./requirements.txt  

	
clean: 
	rm -rf $(BIN)/gcc_lite $(SRC)/{__pycache__,parser.out,parsetab.py}