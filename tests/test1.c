int main()<%

	int int1 = 1234567890;
	int int2 = 0x123aBC;
	int int3 = 0X0123Abc;
	int int4 = 0X0123Abc;
	int int5 = 001123;

	float f1 = 0e6 + 1e+77 + 0e-8;
	float f2 = .0e6 + 1.1e+77 + 1.01e-8 + .123;
	float f3 = 1.e6 + 1.1e+77 + 1.01e-8 + 1.;

	char c1 = 'a';
	char c2 = '\n';

	char s1[] = "Hello World";
	char s2[] = "\n";

	// single line comment
	
	/* multi line
	comment */

	int a = (1+2);
	int b[] = {1,2,3};

	return 0;
%>