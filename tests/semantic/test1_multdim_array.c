// checking multi dim array
int main(){
    int s;
    int *a[4][5][6];
    int *b;
    s=1;
    b = &s;
    a[1][3][4] = b;
    return 0;
}