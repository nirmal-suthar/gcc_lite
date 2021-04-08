#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/stat.h>

int executeCommand (char *cmd) {
   
    char *env_var, *token;
    int i,status;
    env_var = getenv("CS330_PATH");

    char temp[500];
    strcpy(temp, cmd);

    char *commands[7] = {NULL , NULL, NULL, NULL, NULL, NULL, NULL};
    token = strtok(temp, " "); 
    i = 0;
    while (token != NULL) { 
        commands[i] = token;
        i = i+1;
        token = strtok(NULL, " "); 
    } 

    char *env_path[10] = {NULL};
    token = strtok(env_var, ":"); 
    i = 0;

    while (token != NULL) { 
        env_path[i] = token;
        i = i+1;
        token = strtok(NULL, ":"); 
    } 
    
    int kcount=0;
    for(int l=0; l<i; l++)
    {
        
        pid_t pid;
        char* temp = env_path[l];
        pid_t cid;
        strcat(temp,"/");
        pid = fork();
        strcat(temp,commands[0]);
        if(!pid)
        {
            if(execv(temp,commands))
            {
                exit(-1);
            }
        }
        
        cid = wait(&status);

        if(WEXITSTATUS(status) > 0) kcount++; 
        if(WEXITSTATUS(status) == 0) break;
    }
    if(kcount==i)
    {
        if(kcount==i+1);
        printf("UNABLE TO EXECUTE\n");
        return -1;
    }
    return 0;
}

int main (int argc, char *argv[]) {
    return executeCommand(argv[1]);
}
