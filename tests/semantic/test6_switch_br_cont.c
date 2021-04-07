// Chcking break, continue, switch, loops and branches
int main(){
    int x=3,y;
    while(x < 10)
    {
        
        do{
            if(x==7)
                break;
            if(x==5){
                continue;
            }else{
                int b = 1;
                x = 7;  
            }
            
        }while(x>3);

        switch(x){
            case 3: y=7; break; for(int i=0;i<18;i++){ break; }
            default: y =5; break;
            case 'c' : y = 'd';
        }
        break;

    }
    return 0;
}