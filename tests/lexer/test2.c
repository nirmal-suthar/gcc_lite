int main(){
    int ops = 1 + 2 - 3 *5/2% 3;
    int bit = !(1^2|3||4&1&&2<<1>>2);

    ops += 1;
    ops %= 1;
    ops -= 1;
    ops *= 1;
    ops /= 1;

    bit &= 1;    
    bit ^= 1;    
    bit |= 1;    
    bit <<= 1;    
    bit >>= 1;    

    ops++;
    ops--;
    ops += ~1;

    if(1==2 && 1!=2 && 1>2){

    }
    else if(1>=2 && 1<=2 && 1<2){
        ops=bit;
    }
    else{
        ops+=bit;
    }
    
    ops = (bit==0)?1:0;
    return 0;
}