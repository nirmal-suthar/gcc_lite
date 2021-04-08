int x = 10;
static int y = 5;
int main ()
{
    int p,q;
    p = 5;
    q = 5;
    printf("%d%d\n", p,q);
    printf("%d\n", f());
}

/* Module 2: */
int a[10];
int f ()
{
    int k = 0;
    return k++;
}