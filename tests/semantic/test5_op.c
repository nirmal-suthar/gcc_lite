int main()
{
    int c = 4;
    int b = 4;
    float a = c + b;
    char ch = 'a';
    if (c) 
    {
        int d = 1;
        if (d)
            d++;
        else
            d--;
    }
    // printf("%d",&d); scope error line
    a = ch + b;
    // a = a >> 2; //error line;
    // ch = ch | a;//error line;
    // a = a%2;//error line
    return 0;
}