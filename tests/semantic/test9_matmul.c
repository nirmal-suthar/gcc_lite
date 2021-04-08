int main(){  
    //creating two matrices    
int a[3][3];
int b[3][3];
int c[3][3];
int i,j,k;
for(i=0;i<3;i++){
    for(j=0;j<3;j++){
        a[i][j] = i + 1;
        b[i][j] = j + 1;
    }
}
    
//multiplying and printing multiplication of 2 matrices    
    for(i=0;i<3;i++){    
        for(j=0;j<3;j++){    
            c[i][j]=0;
        k = 0;      
            while(k<3)      
            {      
                c[i][j]+=a[i][k]*b[k][j];      
            k++;
            }//end of k loop  
            }//end of j loop  
        printf("\n");
        }
    return 0;	
}