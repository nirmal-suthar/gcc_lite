#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include<fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>


int main(int argc, char* argv[]) {

	int fds[4][2];
	for(int j=0;j<2;j++)
    {
		pid_t pid;
		if(pipe(fds[2*j]) < 0){
		    perror("pipe");
		    exit(-1);
		}

		if(pipe(fds[2*j+1]) < 0){
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
			close(fds[2*j][1]);
			close(fds[2*j+1][0]);

			dup2(fds[2*j][0],0);
			dup2(fds[2*j+1][1],1);

			if(j==0) execl(argv[j+1], "player1",NULL);
			if(j==1) execl(argv[j+1], "player2",NULL);
			
		}

		close(fds[2*j][0]);
		close(fds[2*j+1][1]);	

    }
    int p1_win=0, p2_win=0;
    for(int i=0;i<10;i++)
    {
    	if(write(fds[0][1], "GO", 3)!=3){
            perror("write");
            exit(-1);
        }
        if(write(fds[2][1], "GO", 3)!=3){
            perror("write");
            exit(-1);
        }
        char buf1[32], buf2[32];
		if(read(fds[1][0], buf1, 1) != 1){
			perror("read");
			exit(-1);
	    }
	    if(read(fds[3][0], buf2, 1) != 1){
			perror("read");
			exit(-1);
	    }
	    if(buf1[0]==buf2[0]) continue;
	    if(buf1[0]<buf2[0])
	    {
	    	if(buf2[0]-buf1[0]==1) p2_win++;
	    	else p1_win++;
	    }
	    else
	    {
	    	if(buf1[0]-buf2[0]==1) p1_win++;
	    	else p2_win++;
	    }

    }
    for(int j=0;j<2;j++)
    {
    	close(fds[2*j][1]);
    }
    printf("%d %d", p1_win, p2_win);

    return 0;
}