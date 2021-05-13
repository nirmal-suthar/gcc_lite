// comment
int partition(int* arr, int start, int end) 
{
  int pivot = arr[end];
  int i;
  int j = start-1;
  int tmp;
  int k;
  for (i=start; i<=end-1; i = i + 1) {
    if (arr[i] <= pivot) {
      j = j+1;
      tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }    
  }
  k = j+1;
  tmp = arr[k];
  arr[k] = arr[end];
  arr[end] = tmp;
  return k;
}

int quicksort(int* arr, int start, int end) 
{
  if (start < end) {
    int pi = partition(arr, start, end);
    quicksort(arr, start, pi-1);
    quicksort(arr, pi+1, end);
  } return 1;
}

int main() 
{
  int arr[100];
  int T;
  int i, j, len, k;
  int* a;
  printf("Input the number of test cases : ");
  scanf("%d",&T);
  j=0;

  while (T) {
    T = T-1;
    j = j +1;
    printf("Input the length of the array : ");
    scanf("%d", &len);
    printf("Testcase No. ");
    printf("%d",j);
    printf(": now input the array elements -\n");
    for (i=0; i<len; i = i+1) {
      scanf("%d",&arr[i]);
    }
    // return 0;
    i=0;
    a = &arr[i];
    quicksort(a, 0, len-1);
    printf("sorted array - \n");
    for (i=0; i<len; i=i+1) {
      k = arr[i];
      printf("%d ",k);
    }
    printf("\n");
  }

  return 0;
}
