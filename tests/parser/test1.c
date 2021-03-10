int main() 
{
	char a[100];
	int b = 100;
	int hb=   22;
	int n, exit_m; //Single line comment

	scanf("%s",a);
	printf("String : %s\n",a);

	scanf("%d",&n);
	while(n&1==1)
	{
		printf("hello");
		n ^=1;
	}

	return 0;
}