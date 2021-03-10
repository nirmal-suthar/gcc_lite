PYTHON=python3
SRC=./src
BIN=./bin

all: 
	mkdir -p $(BIN)
	$(PYTHON) -m py_compile $(SRC)/lexer.py $(SRC)/parser.py
	$(PYTHON) $(SRC)/parser.py

	ln -sf $(PWD)/$(SRC)/parser_dot.py $(BIN)/parser
	chmod u+x $(BIN)/parser
	
dep:
	$(PYTHON) -m pip install --ignore-installed -r ./requirements.txt  

	
clean: 
	rm -rf $(BIN)/parser $(SRC)/{__pycache__,parser.out,parsetab.py}