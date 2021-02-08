extern char *name;


typedef struct cs335{
    char name[60];
    int grpno;
    char grade;
} cs335;

int main(){
    cs335 Student_A;
    cs335 *p_Student_A = &Student_A;
    printf("Size of struct %d",sizeof(Student_A));

    if(p_Student_A->grade == Student_A.grade){
        char verdict[] = "PASS";
    }
    else if(p_Student_A->name != Student_A.name){
        char verdict[] = "FAIL\n";
    }
    else{
        char verdict[] = "STILL FAILED";
        int a=0;
        for(int i=0;i<=50;i++){
            a+= i;
            if(a==0){
                continue;
            }            
            else{
                break;
            }
        }
    }

    return 0;
}