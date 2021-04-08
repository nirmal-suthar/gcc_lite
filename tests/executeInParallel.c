#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include<fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

int execute_in_parallel(char *infile, char *outfile)
{
	int fd2, dupfd;
	 
	fd2 = open(outfile, O_RDWR|O_CREAT, 0644);
	if(fd2 < 0){
       perror("open");
       exit(-1);
    }
    dupfd = dup2(fd2, 1);

	int fd, sz; 
	char *c = malloc(3500 * sizeof(char)); 

	fd = open(infile, O_RDONLY); 
	if (fd < 0) { perror("r1"); exit(1); } 

	sz = read(fd, c, 3500); 
	c[sz] = '\0'; 

	char *env_var, *token, *temp, *temp2;
    int i,k;
    env_var = getenv("CS330_PATH");

    char *env_path[3] = {NULL , NULL, NULL};
    token = strtok(env_var, ":"); 
    i = 0;
    while (token != NULL) { 
        env_path[i] = token;
        i = i+1;
        token = strtok(NULL, ":"); 
    }

    char *commands[50] = {NULL};
    token = strtok(c, "\n"); 
    i = 0;
    while (token != NULL) { 
        commands[i] = token;
        i = i+1;
        token = strtok(NULL, "\n"); 
    } 

    int fds[i][2];


    for(int j=0;j<i;j++)
    {
    	char *single_cmd[7] = {NULL , NULL, NULL, NULL, NULL, NULL, NULL};
	    token = strtok(commands[j], " "); 
	    k = 0;
	    while (token != NULL) { 
	    	// puts(token);
	        single_cmd[k] = token;
	        k = k+1;
	        token = strtok(NULL, " "); 
	    } 

	    pid_t pid;
	    if(pipe(fds[j]) < 0){
	        perror("pipe");
	        exit(-1);
	   }


	    pid = fork();
	    if(pid < 0){
	         perror("fork");
	         exit(-1);
	    }
	    if(!pid)
	    {
			close(fds[j][0]);      // Close the read end in child
			// Close the standard output
			dup2(fds[j][1],1);

	    	for(int l=0;l<3;l=l+1)
		    {
		    	 char temp[50],temp2[50];
		    	 strcpy(temp, "/");
		    	 strcpy(temp2, env_path[l]);
		    	 strcat(temp,single_cmd[0]);
		    	 strcat(temp2,temp);
		    	 struct stat sb;
		    	 if ((stat(temp2, &sb) >= 0) && (sb.st_mode > 0) && (S_IEXEC & sb.st_mode))
		    	 {
		    	 	execv(temp2, single_cmd);
		    	 }
		    }
	    	printf("UNABLE TO EXECUTE\n");
	    	exit(-1);
	    }
    }
    for (int j=0; j<i; j=j+1) {
	    wait(NULL);
	    char buf[500];
	    int x = read(fds[j][0], buf, 500);
	    buf[x]='\0';
	    printf("%s",buf);
	}
	return 0;
}

int main(int argc, char *argv[])
{
	return execute_in_parallel(argv[1], argv[2]);
}