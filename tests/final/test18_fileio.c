int main()
{
    int fd_out, x;
    char file_name[10] = "a.txt";
    char msg[20] = "hello world";

    fd_out = fopen(file_name, 2);
    x = fwrite(fd_out, msg , 20);

    fclose(fd_out);

}