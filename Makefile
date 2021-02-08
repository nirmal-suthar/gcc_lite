PYTHON=python3
SRC=./src
BIN=./bin

all:
	mkdir -p $(BIN)
	$(PYTHON) -m pip install --ignore-installed -r ./requirements.txt
	$(PYTHON) -m py_compile $(SRC)/lexer.py
	cp $(SRC)/lexer.sh $(BIN)/lexer
	chmod +x $(BIN)/lexer

clean: 
	rm -rf $(BIN)/lexer $(SRC)/__pycache__