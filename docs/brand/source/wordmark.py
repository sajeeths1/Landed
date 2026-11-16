import sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
f=TTFont(sys.argv[1]); gs=f.getGlyphSet(); cmap=f.getBestCmap(); hm=f['hmtx']
s=236.0/1442; EM=2048*s; SP=0.03*EM
lp=open(sys.argv[2]).read().strip()
old="V200.2Q194.7 186.2 194.4 175.9Q194.1 165.5 193.4 157.8Q192.8 150.2 191.9 145.2Q191 140.1 190 136.7V136H229.3V136.7Q228.3 140.1 227.4 145.2Q226.5 150.2 225.9 157.8Q225.4 165.5 224.9 175.9Q224.5 186.2 224.5 200.2Z"
new="V244C194.7 204 193.7 168 191.8 136H227.4C225.5 168 224.5 204 224.5 244Z"
assert old in lp; lp=lp.replace(old,new)
x=0.0; base=0.0; rest=[]; ymax=0; ymin=0
for i,ch in enumerate("Landed"):
    gn=cmap[ord(ch)]; g=gs[gn]
    bp=BoundsPen(gs); g.draw(bp); ymax=max(ymax,bp.bounds[3]); ymin=min(ymin,bp.bounds[1])
    if i==0:
        ltf=f"translate({x-(190-143*s):.2f} {base-(372-8*s):.2f})"
    else:
        pen=SVGPathPen(gs, ntos=lambda v: ('%.1f'%v).rstrip('0').rstrip('.'))
        g.draw(TransformPen(pen,(s,0,0,-s,x,base))); rest.append(pen.getCommands())
    x+=hm[gn][0]*s+SP
W=x-SP; pad=12
json.dump({"vb":[-pad, -ymax*s-pad, W+2*pad, (ymax-ymin)*s+2*pad], "L":lp, "Ltf":ltf, "rest":"".join(rest), "em":EM}, open(sys.argv[3],"w"))
print(W, ymax*s, ymin*s, EM)
