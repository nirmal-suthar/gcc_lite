int fcreate(char* f);
int fopen(char* f);
int fwrite(int f, char* m);
int fclose(int f);
int fread(int f, int len);

int main()
{
    char* file_name = "a.txt";

    int fd_out = fcreate(file_name);

    char* msg = "hello world";

    fwrite(fd_out, msg);

    fclose(fd_out);

    int fd_in = fopen(file_name);

    fread(fd_in, 5);
}