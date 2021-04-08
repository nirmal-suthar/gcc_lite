#include<types.h>
#include<context.h>
#include<file.h>
#include<lib.h>
#include<serial.h>
#include<entry.h>
#include<memory.h>
#include<fs.h>
#include<kbd.h>


/************************************************************************************/
/***************************Do Not Modify below Functions****************************/
/************************************************************************************/

void free_file_object(struct file *filep)
{
	if(filep)
	{
		os_page_free(OS_DS_REG ,filep);
		stats->file_objects--;
	}
}

struct file *alloc_file()
{
	struct file *file = (struct file *) os_page_alloc(OS_DS_REG); 
	file->fops = (struct fileops *) (file + sizeof(struct file)); 
	bzero((char *)file->fops, sizeof(struct fileops));
	file->ref_count = 1;
	file->offp = 0;
	stats->file_objects++;
	return file; 
}

void *alloc_memory_buffer()
{
	return os_page_alloc(OS_DS_REG); 
}

void free_memory_buffer(void *ptr)
{
	os_page_free(OS_DS_REG, ptr);
}

/* STDIN,STDOUT and STDERR Handlers */

/* read call corresponding to stdin */

static int do_read_kbd(struct file* filep, char * buff, u32 count)
{
	kbd_read(buff);
	return 1;
}

/* write call corresponding to stdout */

static int do_write_console(struct file* filep, char * buff, u32 count)
{
	struct exec_context *current = get_current_ctx();
	return do_write(current, (u64)buff, (u64)count);
}

long std_close(struct file *filep)
{
	filep->ref_count--;
	if(!filep->ref_count)
		free_file_object(filep);
	return 0;
}
struct file *create_standard_IO(int type)
{
	struct file *filep = alloc_file();
	filep->type = type;
	if(type == STDIN)
		filep->mode = O_READ;
	else
		filep->mode = O_WRITE;
	if(type == STDIN){
		filep->fops->read = do_read_kbd;
	}else{
		filep->fops->write = do_write_console;
	}
	filep->fops->close = std_close;
	return filep;
}

int open_standard_IO(struct exec_context *ctx, int type)
{
	int fd = type;
	struct file *filep = ctx->files[type];
	if(!filep){
		filep = create_standard_IO(type);
	}else{
		filep->ref_count++;
		fd = 3;
		while(ctx->files[fd])
			fd++; 
	}
	ctx->files[fd] = filep;
	return fd;
}
/**********************************************************************************/
/**********************************************************************************/
/**********************************************************************************/
/**********************************************************************************/

/* File exit handler */
void do_file_exit(struct exec_context *ctx)
{
	for(int i=0;i<MAX_OPEN_FILES;i++)
	{
		do_file_close(ctx->files[i]);
	}
	/*TODO the process is exiting. Adjust the refcount
	of files*/
}

/*Regular file handlers to be written as part of the assignmemnt*/


static int do_read_regular(struct file *filep, char * buff, u32 count)
{
	if(filep==NULL || filep->inode==NULL) return -EINVAL;
	if((filep->mode & O_READ)==0) return -EACCES;
	int size= flat_read(filep->inode, buff, count, &(filep->offp));
	filep->offp+=size;
	return size;
	/** 
	*  TODO Implementation of File Read, 
	*  You should be reading the content from File using file system read function call and fill the buf
	*  Validate the permission, file existence, Max length etc
	*  Incase of Error return valid Error code 
	**/
	// int ret_fd = -EINVAL; 
	// return ret_fd;
}

/*write call corresponding to regular file */

static int do_write_regular(struct file *filep, char * buff, u32 count)
{
	if(filep==NULL || filep->inode==NULL) return -EINVAL;
	if((filep->mode & O_WRITE)==0) return -EACCES;
	int size= flat_write(filep->inode, buff, count, &(filep->offp));
	filep->offp+=size;
	return size;
	/** 
	*   TODO Implementation of File write, 
	*   You should be writing the content from buff to File by using File system write function
	*   Validate the permission, file existence, Max length etc
	*   Incase of Error return valid Error code 
	* */
	// int ret_fd = -EINVAL; 
	// return ret_fd;
}

long do_file_close(struct file *filep)
{
	if(filep==NULL) return -EINVAL;
	filep->ref_count--;
	free_file_object(filep);
	return 0;

	/** TODO Implementation of file close  
	*   Adjust the ref_count, free file object if needed
	*   Incase of Error return valid Error code 
	*/
	// return -EINVAL;
}

static long do_lseek_regular(struct file *filep, long offset, int whence)
{
	if(!filep) return -EINVAL;
	if(whence== 2)
	{
		filep->offp = filep->inode->max_pos + offset;
		if(offset>0 ) return -EINVAL;  
	}
	else if(whence== 0)
	{
		filep->offp = offset;
		if(filep->offp > FILE_SIZE) return -EINVAL;  
	}
	else if(whence== 1)
	{
		filep->offp = filep->offp + offset;
		if(filep->offp > FILE_SIZE) return -EINVAL; 	
	}

	return filep->offp;


	/** 
	*   TODO Implementation of lseek 
	*   Set, Adjust the ofset based on the whence
	*   Incase of Error return valid Error code 
	* */
	// int ret_fd = -EINVAL; 
	// return ret_fd;
}

extern int do_regular_file_open(struct exec_context *ctx, char* filename, u64 flags, u64 mode)
{
	// return 5;
	struct inode* temp= lookup_inode(filename);
	int iscreate = 0;
	if(flags & O_CREAT) iscreate = 1;
	if(temp==NULL)
	{
		// printf("I am in NULL\n");
		if(iscreate)
		{
			temp = create_inode(filename, mode);
		}
		else
		{
			return -EINVAL;
		}
	}
	// printf("I am Outside\n");
	int i=3;
	while(i< MAX_OPEN_FILES && ctx->files[i]!=NULL) i++;
	if(i==MAX_OPEN_FILES) return -EINVAL;

	// printf("Value of i is - %d\n",i);

	ctx->files[i]= alloc_file();

	ctx->files[i]->inode = temp;
	ctx->files[i]->type = REGULAR;
	ctx->files[i]->mode = flags;
	ctx->files[i]->pipe = NULL;
	ctx->files[i]->msg_queue = NULL;
	ctx->files[i]->fops->read = do_read_regular;
	ctx->files[i]->fops->write = do_write_regular;
	ctx->files[i]->fops->lseek = do_lseek_regular;
	ctx->files[i]->fops->close = do_file_close;

	return i;
// type - regular
	// mode - flags
	//pipe null

	/**  
	*  TODO Implementation of file open, 
	*  You should be creating file(use the alloc_file function to creat file), 
	*  To create or Get inode use File system function calls, 
	*  Handle mode and flags 
	*  Validate file existence, Max File count is 16, Max Size is 4KB, etc
	*  Incase of Error return valid Error code 
	* */
	
}

/**
 * Implementation dup 2 system call;
 */
int fd_dup2(struct exec_context *current, int oldfd, int newfd)
{
	if(current->files[oldfd]==NULL || current->files[oldfd]->inode==NULL) return -EINVAL;
	if(current->files[newfd]!=NULL && current->files[newfd]->inode!=NULL)
	{
		do_file_close(current->files[newfd]);
	}
	current->files[newfd]=current->files[oldfd];
	/** 
	*  TODO Implementation of the dup2 
	*  Incase of Error return valid Error code 
	**/
	// int ret_fd = -EINVAL; 
	return newfd;
}

int do_sendfile(struct exec_context *ctx, int outfd, int infd, long *offset, int count) {
	
	if(ctx->files[infd]==NULL) return -EINVAL;
	if(ctx->files[outfd]==NULL) return -EINVAL;

	char *buffer= (char *)alloc_memory_buffer();

	if((ctx->files[outfd]->mode & O_WRITE)==0) return -EACCES; 
	
	int x;

	if((ctx->files[infd]->mode & O_READ)==0) return -EACCES;

	if(!offset)
	{
		x= flat_read(ctx->files[infd]->inode, buffer, count, &(ctx->files[infd]->offp));
		ctx->files[infd]->offp += x;
	}
	else
	{
		x= flat_read(ctx->files[infd]->inode, buffer, count, (int *)offset);
		offset += x;
	}

	int y= flat_write(ctx->files[outfd]->inode, buffer, x, &(ctx->files[outfd]->offp));

	free_memory_buffer((void *)buffer);

	return y;
}

