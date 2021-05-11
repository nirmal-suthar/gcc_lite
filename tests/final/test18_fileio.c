int fcreate(int f);
int fopen(int f);
int fwrite(int f, int m);
int fclose(int f);
int fread(int f, int len);

int main()
{
    int file_name = "a.txt";

    int fd_out = fcreate(file_name);

    int msg = "hello world";

    fwrite(fd_out, msg);

    fclose(fd_out);

    int fd_in = fopen(file_name);

    fread(fd_in, 5);
}