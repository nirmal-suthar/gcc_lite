int main()
{
    int O_CREAT = 64;
    int O_RDWD = 2;
    int O_RDONLY = 0;
    int O_WRONLY = 1;

    int fd, x;
    char msg[20] = "hello world";
    fd = open("fileio.txt", O_CREAT | O_RDWD); 
    x = write(fd, msg , strlen(msg)+1);
    printf("length of buffer: %d", strlen(msg)+1);
    close(fd);
}