#include <msg_queue.h>
#include <context.h>
#include <memory.h>
#include <file.h>
#include <lib.h>
#include <entry.h>



/************************************************************************************/
/***************************Do Not Modify below Functions****************************/
/************************************************************************************/

struct msg_queue_info *alloc_msg_queue_info()
{
	struct msg_queue_info *info;
	info = (struct msg_queue_info *)os_page_alloc(OS_DS_REG);
	
	if(!info){
		return NULL;
	}
	return info;
}

void free_msg_queue_info(struct msg_queue_info *q)
{
	os_page_free(OS_DS_REG, q);
}

struct message *alloc_buffer()
{
	struct message *buff;
	buff = (struct message *)os_page_alloc(OS_DS_REG);
	if(!buff)
		return NULL;
	return buff;	
}

void free_msg_queue_buffer(struct message *b)
{
	os_page_free(OS_DS_REG, b);
}

/**********************************************************************************/
/**********************************************************************************/
/**********************************************************************************/
/**********************************************************************************/


int do_create_msg_queue(struct exec_context *ctx)
{
	int i=3;
	while(i< MAX_OPEN_FILES && ctx->files[i]!=NULL) i++;
	if(i==MAX_OPEN_FILES) return -ENOMEM;

	// printf("Value of i is - %d\n",i);

	ctx->files[i]= alloc_file();

	ctx->files[i]->inode = NULL;
	ctx->files[i]->type = MSG_QUEUE;
	ctx->files[i]->pipe = NULL;
	ctx->files[i]->fops = NULL;

	ctx->files[i]->msg_queue = alloc_msg_queue_info();

	ctx->files[i]->msg_queue->msg_buffer = alloc_buffer();
	ctx->files[i]->msg_queue->count_msg=0;
	ctx->files[i]->msg_queue->count_block=0;

	ctx->files[i]->msg_queue->members.member_pid[0]= ctx->pid;
	ctx->files[i]->msg_queue->members.member_count=1;
	/** 
	 * TODO Implement functionality to
	 * create a message queue
	 **/
	return i;
}


int do_msg_queue_rcv(struct exec_context *ctx, struct file *filep, struct message *msg)
{
	if(filep->type!=MSG_QUEUE) return -EINVAL;
	int n= filep->msg_queue->count_msg;
	for(int i=0;i<n;i++)
	{
		if(filep->msg_queue->msg_buffer[i].to_pid==ctx->pid )
		{
			msg->from_pid = filep->msg_queue->msg_buffer[i].from_pid;
			msg->to_pid = filep->msg_queue->msg_buffer[i].to_pid;
			for(int k=0;k<MAX_TXT_SIZE;k++) msg->msg_txt[k] = filep->msg_queue->msg_buffer[i].msg_txt[k];

			while(i<n-1)
			{
				filep->msg_queue->msg_buffer[i].from_pid = filep->msg_queue->msg_buffer[i+1].from_pid;
				filep->msg_queue->msg_buffer[i].to_pid = filep->msg_queue->msg_buffer[i+1].to_pid;
				for(int k=0;k<MAX_TXT_SIZE;k++) filep->msg_queue->msg_buffer[i].msg_txt[k] = filep->msg_queue->msg_buffer[i+1].msg_txt[k];
				i++;
			}
			filep->msg_queue->count_msg--;
			return 1;
		}
		// if(filep->msg_queue->msg_buffer[i].to_pid==BROADCAST_PID && filep->msg_queue->msg_buffer[i].from_pid!=ctx->pid)
		// {
		// 	//check if block happens or not
			// int is_block=0;
			// for(int j=0;j<filep->msg_queue->count_block;j++)
			// {
			// 	if(filep->msg_queue->blocker[j][0]==ctx->pid && filep->msg_queue->blocker[j][1]==msg->from_pid)
			// 	{
			// 		is_block=1;
			// 		break;
			// 	}
			// }
		// 	if(is_block==0)
		// 	{
		// 		msg= &(filep->msg_queue->msg_buffer[i]);
		// 		return 1;
		// 	}
			
		// }
	}
	return 0;
	/** 
	 * TODO Implement functionality to
	 * recieve a message
	 **/
	// return -EINVAL;
}


int do_msg_queue_send(struct exec_context *ctx, struct file *filep, struct message *msg)
{
	if(filep->type!=MSG_QUEUE) return -EINVAL;
	int is_member=0;

	int xid = ctx->pid;
	int fid, tid;
	fid = msg->from_pid;
	tid = msg->to_pid;

	if(tid==BROADCAST_PID)
	{
		int xyz=0;
		for(int i=0;i<filep->msg_queue->members.member_count;i++)
		{
			if(filep->msg_queue->members.member_pid[i]!=fid)
			{
				int yid = filep->msg_queue->members.member_pid[i];
				int is_block=0;
				for(int j=0;j<filep->msg_queue->count_block;j++)
				{
					if(filep->msg_queue->blocker[j][0]==yid && filep->msg_queue->blocker[j][1]==xid)
					{
						is_block=1;
						break;
					}
				}				
				if(is_block==0)
				{
					xyz++;
					int y= filep->msg_queue->count_msg;
					filep->msg_queue->msg_buffer[y].from_pid= xid;
					filep->msg_queue->msg_buffer[y].to_pid= yid;
					for(int k=0;k<MAX_TXT_SIZE;k++) filep->msg_queue->msg_buffer[y].msg_txt[k]= msg->msg_txt[k];
					filep->msg_queue->count_msg++;
				}
			}
		}
		return xyz;
	}
	else
	{
		for(int i=0;i<filep->msg_queue->members.member_count;i++)
		{
			if(filep->msg_queue->members.member_pid[i]==tid)
			{
				is_member=1;
				break;
			}
		}
		int is_block=0;
		for(int j=0;j<filep->msg_queue->count_block;j++)
		{
			if(filep->msg_queue->blocker[j][0]==tid && filep->msg_queue->blocker[j][1]==fid)
			{
				is_block=1;
				break;
			}
		}
		if(is_block==1 || is_member==0)
		{
			return -EINVAL;
		}
		else
		{
			int y= filep->msg_queue->count_msg;
			filep->msg_queue->msg_buffer[y].from_pid= fid;
			filep->msg_queue->msg_buffer[y].to_pid= tid;
			for(int k=0;k<MAX_TXT_SIZE;k++) filep->msg_queue->msg_buffer[y].msg_txt[k]= msg->msg_txt[k];
			filep->msg_queue->count_msg++;
			return 1;
		}
	}
	/** 
	 * TODO Implement functionality to
	 * send a message
	 **/
	return 0;
}

void do_add_child_to_msg_queue(struct exec_context *child_ctx)
{
	for(int i=0;i<MAX_OPEN_FILES;i++)
	{
		if(child_ctx->files[i]!=NULL && child_ctx->files[i]->type==MSG_QUEUE)
		{
			if(child_ctx->files[i]->msg_queue->members.member_count==MAX_MEMBERS) 
			{
				//do nothing
			}
			else
			{
				int x= child_ctx->files[i]->msg_queue->members.member_count;
				child_ctx->files[i]->msg_queue->members.member_pid[x]=child_ctx->pid;
				child_ctx->files[i]->msg_queue->members.member_count++;
			}
		}
	}
	/** 
	 * TODO Implementation of fork handler 
	 **/
}

void do_msg_queue_cleanup(struct exec_context *ctx)
{
	int i=0;
	while(i< MAX_OPEN_FILES) 
	{
		if(ctx->files[i]!=NULL && ctx->files[i]->type==MSG_QUEUE)
		{
			do_msg_queue_close(ctx,i);
		}
		i++;
	}
	/** 
	 * TODO Implementation of exit handler 
	 **/
}

int do_msg_queue_get_member_info(struct exec_context *ctx, struct file *filep, struct msg_queue_member_info *info)
{
	if(filep==NULL || filep->type!=MSG_QUEUE) return -EINVAL;
	info->member_count = filep->msg_queue->members.member_count;
	int i=0;
	while(i<info->member_count)
	{
		info->member_pid[i]= filep->msg_queue->members.member_pid[i];
		i++;
	}
	return 0;
	/** 
	 * TODO Implementation of exit handler 
	 **/
	// return -EINVAL;
}


int do_get_msg_count(struct exec_context *ctx, struct file *filep)
{

	// TODO
	if(filep==NULL || filep->type!=MSG_QUEUE) return -EINVAL;
	int i=0,ans=0,n;
	n = filep->msg_queue->count_msg;
	while(i<n)
	{
		if(filep->msg_queue->msg_buffer[i].to_pid==ctx->pid) ans++;
		i++;
	}
	return ans;
	/** 
	 * TODO Implement functionality to
	 * return pending message count to calling process
	 **/
	// return 0;
}

int do_msg_queue_block(struct exec_context *ctx, struct file *filep, int pid)
{
	if(filep==NULL || filep->type!=MSG_QUEUE) return -EINVAL;
	int is_member=0;

	int xid = ctx->pid;

	for(int i=0;i<filep->msg_queue->members.member_count;i++)
	{
		if(filep->msg_queue->members.member_pid[i]==pid)
		{
			is_member=1;
			break;
		}
	}
	if(is_member==0)
	{
		return -EINVAL;
	}
	else
	{
		filep->msg_queue->blocker[filep->msg_queue->count_block][0]=xid;
		filep->msg_queue->blocker[filep->msg_queue->count_block][1]=pid;
		filep->msg_queue->count_block++;
		return 0;
	}
	/** 
	 * TODO Implement functionality to
	 * block messages from another process 
	 **/
	// return -EINVAL;
}

int do_msg_queue_close(struct exec_context *ctx, int fd)
{
	if(ctx->files[fd]->type!=MSG_QUEUE) return -EINVAL;

	int n= ctx->files[fd]->msg_queue->members.member_count;
	if(n==1)
	{
		free_msg_queue_buffer(ctx->files[fd]->msg_queue->msg_buffer);
		free_msg_queue_info(ctx->files[fd]->msg_queue);
	}
	else
	{
		//TODO 
		// block table update
		// messege table update
		int blocker2[12][2];
		int count_block2 = 0;

		for(int j=0;j< ctx->files[fd]->msg_queue->count_block;j++)
		{
			if(ctx->files[fd]->msg_queue->blocker[j][0]!=ctx->pid && ctx->files[fd]->msg_queue->blocker[j][1]!=ctx->pid )
			{
				blocker2[count_block2][0]= ctx->files[fd]->msg_queue->blocker[j][0];
				blocker2[count_block2][1]= ctx->files[fd]->msg_queue->blocker[j][1];
				count_block2++;
			}
		}
		for(int j=0;j< count_block2;j++)
		{
			ctx->files[fd]->msg_queue->blocker[j][0] = blocker2[j][0];
			ctx->files[fd]->msg_queue->blocker[j][1] = blocker2[j][1];
		}
		ctx->files[fd]->msg_queue->count_block = count_block2;

		struct message *msg_buffer2 =alloc_buffer();
		int count_msg2 = 0;

		for(int j=0;j< ctx->files[fd]->msg_queue->count_msg;j++)
		{
			if(ctx->files[fd]->msg_queue->msg_buffer[j].to_pid != ctx->pid )
			{
				msg_buffer2[count_msg2].from_pid = ctx->files[fd]->msg_queue->msg_buffer[j].from_pid;
				msg_buffer2[count_msg2].to_pid = ctx->files[fd]->msg_queue->msg_buffer[j].to_pid;
				for(int k=0;k<MAX_TXT_SIZE;k++) msg_buffer2[count_msg2].msg_txt[k] = ctx->files[fd]->msg_queue->msg_buffer[j].msg_txt[k];
				count_msg2++;
			}
		}
		for(int j=0;j< count_msg2;j++)
		{
			ctx->files[fd]->msg_queue->msg_buffer[j].from_pid = msg_buffer2[j].from_pid;
			ctx->files[fd]->msg_queue->msg_buffer[j].to_pid = msg_buffer2[j].to_pid;
			for(int k=0;k<MAX_TXT_SIZE;k++) ctx->files[fd]->msg_queue->msg_buffer[j].msg_txt[k] = msg_buffer2[j].msg_txt[k];
		}
		ctx->files[fd]->msg_queue->count_msg = count_msg2;

		int i=0;
		while(ctx->files[fd]->msg_queue->members.member_pid[i]!=ctx->pid) i++;

		while(i<n-1) 
		{
			ctx->files[fd]->msg_queue->members.member_pid[i] = ctx->files[fd]->msg_queue->members.member_pid[i+1];
			i++;
		}
		ctx->files[fd]->msg_queue->members.member_count--;
	}
	/** 
	 * TODO Implement functionality to
	 * remove the calling process from the message queue 
	 **/
	return 0;
}
