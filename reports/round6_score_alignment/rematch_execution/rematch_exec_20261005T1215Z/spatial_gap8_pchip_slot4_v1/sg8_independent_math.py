"""Independent coefficient reconstruction. Never imports production math."""
from fractions import Fraction as Q


def rebuild(q,z,frame):
    if len(q)!=4 or len(z)!=4:
        raise ValueError('four independent supports required')
    h=[q[1]-q[0],q[2]-q[1],q[3]-q[2]]
    if len(q)!=4 or len(z)!=4 or h[1]!=8 or any(not 1<=v<=8 for v in [h[0],h[2]]) or not q[1]<=frame<=q[2]:
        raise ValueError('invalid independent geometry')
    differences=[Q(z[i+1]-z[i],h[i]) for i in range(3)]
    derivatives=[]
    for j in [1,2]:
        a,b=differences[j-1],differences[j]
        if a==0 or b==0 or (a>0)!=(b>0):
            derivatives.append(Q(0))
        else:
            # Algebraically expanded numerator/denominator, not production basis.
            derivatives.append(Q(3*(h[j-1]+h[j]))*a*b/
                ((2*h[j]+h[j-1])*b+(h[j]+2*h[j-1])*a))
    dleft,dright=derivatives
    distance=frame-q[1]
    c0=Q(z[1]);c1=dleft
    c2=Q(3*(z[2]-z[1]),64)-(2*dleft+dright)/8
    c3=Q(2*(z[1]-z[2]),512)+(dleft+dright)/64
    exact=((c3*distance+c2)*distance+c1)*distance+c0
    # Integer quotient/remainder half-even independent of built-in round.
    numerator,denominator=exact.numerator,exact.denominator
    base,remainder=divmod(numerator,denominator)
    if 2*remainder>denominator or (2*remainder==denominator and base%2):
        base+=1
    return exact,base
