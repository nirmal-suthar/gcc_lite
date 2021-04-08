#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <sys/types.h>
// #include <sys/stat.h>

#define ROCK        0 
#define PAPER       1 
#define SCISSORS    2 

#define STDIN 		0
#define STDOUT 		1
#define STDERR		2


#include "gameUtils.h"

int getWalkOver(int numPlayers); // Returns a number between [1, numPlayers]

// It uses strtok to find final name from path of a file
char* namefinal(char *playerpath)
{
	char *token;
	char *directory[100] = {NULL};
    token = strtok(playerpath, "/"); 
    int i = 0;
    while (token != NULL) { 
        directory[i] = token;
        i = i+1;
        token = strtok(NULL, "/"); 
    }
    return directory[i-1];
}

/*
This is the main program 
n- no. of players
rn- no. of rounds to play in one on one battle
player_name - it contains the directory of executable
defeated- it is an array where 0 indicates ith player not defeted
*/
void solver(int n, int rn, char *player_name[], int defeated[], int fds[][2])
{
	//print players 
	int flag=0;
	for(int i=0;i<n;i++)
	{
		if(defeated[i]==0 && !flag) 
		{
			printf("p%d",i);
			flag=1;
		}
		else if(defeated[i]==0) 
		{
			printf(" p%d",i);
		}
	}

	//count nap- number of active players
	int nap=0,walkover=-2,x,i;
	for(i=0;i<n;i++)
	{
		if(defeated[i]==0) nap++;
	}
	if(nap<=1) 
	{
		for(int j=0;j<n;j++)
		{
			close(fds[2*j][1]);
		}	
		return;
	}

	printf("\n");
	// Do walkover
	if(nap%2==1)
	{
		x= getWalkOver(nap);
		for(i=0;i<n && x>0;i++)
		{
			if(defeated[i]==0) x--;
		}
		walkover = i-1;
	}

	int l= (nap/2) +1 ;
	int first_ele[l];
	int second_ele[l];
	int win_points[n];
	for(i=0;i<n;i++) win_points[i]=0;
	
	int k=0;
	for(i=0;i<n;i++)
	{
		if(defeated[i]==0 && i!=walkover)
		{
			int j=i+1;
			while(j<n && (defeated[j]!=0 || j==walkover)) j++;
			if(j==n) continue;
			//do the match
			first_ele[k]=i;
			second_ele[k]=j;
			k++;
			i=j;
		}
	}

	if(nap==n)
	{
		pid_t pid[n];
		//creating processes and pipes
		for(int j=0;j<n;j++)
	    {
			if(pipe(fds[2*j]) < 0){
			    perror("pipe");
			    exit(-1);
			}

			if(pipe(fds[2*j+1]) < 0){
			    perror("pipe");
			    exit(-1);
			}

			pid[j] = fork();
			if(pid[j] < 0){
			     perror("fork");
			     exit(-1);
			}
			if(!pid[j])
			{
				close(fds[2*j][1]);
				close(fds[2*j+1][0]);

				dup2(fds[2*j][0],0);
				dup2(fds[2*j+1][1],1);

				char buff1[10000],buff2[10000];
				int idx = 0;
				for(idx=0; player_name[j+1][idx]!='\0'; idx++)
				{
					buff1[idx] = player_name[j+1][idx];
					buff2[idx] = player_name[j+1][idx];
				}
				buff1[idx] = '\0';
				buff2[idx] = '\0';

				execl(buff1, namefinal(buff2),NULL);
			}
			close(fds[2*j][0]);
			close(fds[2*j+1][1]);
	    }
	}

	

	for(int i=0;i<rn;i++)
	{
		for(int j=0;j<k;j++)
		{
			int x,y;
			x = first_ele[j];
			y = second_ele[j];

			if(write(fds[2*x][1], "GO", 3)!=3){
	            perror("write");
	            exit(-1);
	        }
	        if(write(fds[2*y][1], "GO", 3)!=3){
	            perror("write");
	            exit(-1);
	        }
	        char buf1[32], buf2[32];
			if(read(fds[2*x+1][0], buf1, 1) != 1){
				perror("read");
				exit(-1);
		    }
		    if(read(fds[2*y+1][0], buf2, 1) != 1){
				perror("read");
				exit(-1);
		    }
		    if(buf1[0]==buf2[0]) continue;
		    if(buf1[0]<buf2[0])
		    {
		    	if(buf2[0]-buf1[0]==1) win_points[y]++;
		    	else win_points[x]++;
		    }
		    else
		    {
		    	if(buf1[0]-buf2[0]==1) win_points[x]++;
		    	else win_points[y]++;
		    }
		}
	}

	for(int j=0;j<k;j++)
	{
		int x=first_ele[j];
		int y=second_ele[j];

		if(win_points[x]>=win_points[y])
		{
			defeated[y]=1;
		}
		else defeated[x]=1;
	}

	return solver(n, rn, player_name, defeated, fds);
}

int main(int argc, char *argv[])
{
	int rn;
	if(argc==2) rn=10;
	else rn= atoi(argv[2]);

	//Taking the input
	int fd, sz; 
	char *c = malloc(10000 * sizeof(char)); 

	fd = open(argv[argc-1], O_RDONLY); 
	if (fd < 0) { perror("r1"); exit(1); } 

	sz = read(fd, c, 10000); 
	c[sz] = '\0';

	char *token;
	char *player_name[100] = {NULL};
    token = strtok(c, "\n"); 
    int i = 0;
    while (token != NULL) { 
        player_name[i] = token;
        i = i+1;
        token = strtok(NULL, "\n"); 
    } 
    //Finish Taking Input

    int n= atoi(player_name[0]);
    int defeated[n];
    int fds[200][2];
    for(int i=0;i<n;i++) defeated[i]=0;

    solver(n, rn, player_name, defeated, fds);

	return 0;
}