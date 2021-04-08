int main() 
{
    int a[10][10][10];
    int i,j,k;
    for (i = 0; i=10; i = i + 1){
			for ( j=0; j=10; j = j + 1){
				for (k=0; k=10; k++){
					a[i][j][k] /= (i - j)*-k;
				}
			}
		}
}