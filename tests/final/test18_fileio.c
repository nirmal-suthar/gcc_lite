int main()
{
    int fd_out, x;
    char file_name[10] = "a.txt";
    char msg[20] = "hello world";

    fd_out = open(file_name, 2);
    x = write(fd_out, msg , strlen(msg)+1);

    close(fd_out);

}