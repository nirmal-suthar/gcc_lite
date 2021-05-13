int indexOf(int r, int c, int i, int j) {
  return i*r + j;
}

int main() {

  int a[100], b[100], c[100];
  int r1, c1, r2, c2, idx;
  int i, j, k=0;

  int na, nb, nc;

  //scanmat(a0, &r1, &c1);
  printf("Input matrix size (m,n) ");
  scanf("%d", &r1);
  scanf("%d", &c1);
  printf("Enter matrix elements:\n");
  for (i=0; i<r1; i=i+1) {
    for (j=0; j<c1; j=j+1) {
      idx = indexOf(r1, c1, i, j);
      scanf("%d", &a[idx]);
    }
  }

  //scanmat(b0, &r2, &c2);
  printf("Input matrix size (m,n) ");
  scanf("%d", &r2);
  scanf("%d", &c2);
  printf("Enter matrix elements:\n");
  for (i=0; i<r2; i=i+1) {
    for (j=0; j<c2; j=j+1) {
      idx = indexOf(r2, c2, i, j);
      scanf("%d",&b[idx]);
    }
  }

  //matmul(a0, r1, c1, b0, c2, c0);
  for (i=0; i<r1; i=i+1) {
    for (j=0; j<c2; j=j+1) {
      nc = indexOf(r1, c2, i, j);
      c[nc] = 0;
      for (k=0; k<c1; k=k+1) {
        na = indexOf(r1, c1, i, k);
        nb = indexOf(c1, c2, k, j);
        c[nc] += a[na]*b[nb];
      }
    }
  }  

  printf("Matrix product:\n");
  //printmat(c0, r1, c2);
  for (i=0; i<r1; i=i+1) {
    for (j=0; j<c2; j=j+1) {
      idx = indexOf(r1, c2, i, j);
      printf("%d ",c[idx]);
    }
    printf("\n");
  }

  return 0;
}
