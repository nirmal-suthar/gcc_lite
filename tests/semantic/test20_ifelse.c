int main() 
{
		int a = 1;
		int b = 2;
		int c = 3;
		int d = 4;
		int e = 5;
		int f = 6;
		if (a > b) {
			a = b + 1;
			if (c > a){
				c = a - 1;
			}
			else if (c < a) {
				c = a + 1;
				if (c==d && e!=f) {
					if (a) {
						a = e;
					} else {
						a = f;
					}
				}
				if (c!=d || e>f) {
					if (a) {
						a = e;
					} else {
						a = f;
					}
				}
			}
			else{
				c = a * 2;
			}
		}
		else if (a<b){
			a = b * 2;
		}
		else{
			return;
		
        }
}