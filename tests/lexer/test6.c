struct Node { 
	int data; 
	struct Node* next; 
}; 

int main() 
{ 	
	int a, b = 1;
	struct Node* head = NULL; 
	struct Node* second = NULL; 
	struct Node* third = NULL; 
	head = (struct Node*)malloc(100*sizeof(struct Node)); 
	second = (struct Node*)malloc(sizeof(struct Node)); 
	third = (struct Node*)malloc(sizeof(struct Node)); 

	head->data = 1; // assign data in first node 
	head->next = second; // Link first node with 
	second->data = 2; 

	// Link second node with the third node 
	second->next = third;

	third->data = 3; // assign data to third node 
	third->next = NULL; 

	return 0; 
}