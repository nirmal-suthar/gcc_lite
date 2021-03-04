PYTHON=python3
SRC=./src
BIN=./bin

all:
	mkdir -p $(BIN)
	$(PYTHON) -m pip install --user --ignore-installed -r ./requirements.txt  
	$(PYTHON) -m py_compile $(SRC)/lexer.py $(SRC)/parser.py
	$(PYTHON) $(SRC)/parser.py
	cp $(SRC)/lexer.sh $(BIN)/lexer
	cp $(SRC)/parser.sh $(BIN)/parser
	chmod +x $(BIN)/lexer
	chmod +x $(BIN)/parser

clean: 
	rm -rf $(BIN)/lexer $(BIN)/parser $(SRC)/__pycache__