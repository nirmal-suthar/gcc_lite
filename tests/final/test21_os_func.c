int fork();

int main()
{
    int pid;
    pid = fork();
    if(pid==0){
        printf("Child process! pid=%d\n",pid);
    }
    else{
        printf("Parent process! pid=%d\n",pid);
    }
    
    return 0;
}
