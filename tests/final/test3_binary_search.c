int main()
{
   int c, first, last, middle, n, search, array[100];
 
   printf("Enter number of elements\n");
   scanf("%d", &n);

   printf("Enter ");
   printf("%d",n);
   printf(" integers\n");
 
   for (c = 0; c < n; c=c+1){
      scanf("%d", &array[c]);
   }
   printf("Enter value to find\n");
   scanf("%d", &search);
   

   first = 0;
   last = n - 1;
   middle = (first+last)/2;
 
   while (first <= last) {
      if (array[middle] < search)
         first = middle + 1;    
      else if (array[middle] == search) {
         printf("%d",search);
         printf(" found at location ");
         printf("%d",middle+1);
         printf("\n");
         break;
      }
      else
         last = middle - 1;
 
      middle = (first + last)/2;
   }
   if (first > last){
      printf("Not found! ");
      printf("%d",search);
      printf(" is not present in the list.\n");
  }
 
   return 0;   
}