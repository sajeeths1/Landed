import sys, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
f=TTFont(sys.argv[1]); gs=f.getGlyphSet(); cmap=f.getBestCmap(); hm=f['hmtx']
s=float(sys.argv[3]); x=float(sys.argv[4]); base=float(sys.argv[5]); EM=2048*s; SP=0.03*EM
out=[]
BOWL=float(sys.argv[6]) if len(sys.argv)>6 else 1.0     # how much further the last d's bowl sticks out
class BowlPen:
    """Stretch everything left of the d's stem away from the stem; the stem itself is untouched."""
    def __init__(self,o,xs,k): self.o=o; self.xs=xs; self.k=k
    def m(self,p): return None if p is None else ((self.xs-(self.xs-p[0])*self.k if p[0]<self.xs else p[0]), p[1])
    def moveTo(self,p): self.o.moveTo(self.m(p))
    def lineTo(self,p): self.o.lineTo(self.m(p))
    def qCurveTo(self,*ps): self.o.qCurveTo(*[self.m(p) for p in ps])
    def curveTo(self,*ps): self.o.curveTo(*[self.m(p) for p in ps])
    def closePath(self): self.o.closePath()
    def endPath(self): self.o.endPath()
for i,ch in enumerate("anded"):
    gn=cmap[ord(ch)]; g=gs[gn]
    bp=BoundsPen(gs); g.draw(bp); b=bp.bounds
    pen=SVGPathPen(gs, ntos=lambda v: ('%.1f'%v).rstrip('0').rstrip('.'))
    if i==4 and BOWL!=1.0:
        xs=b[2]-270                                  # just left of the stem
        grow=(xs-b[0])*(BOWL-1)                      # extra bowl width, font units
        x+=grow*s                                    # keep the gap to the e unchanged
        g.draw(BowlPen(TransformPen(pen,(s,0,0,-s,x,base)),xs,BOWL))
        out.append({"ch":ch,"d":pen.getCommands(),"x0":x+(b[0]-grow)*s,"x1":x+b[2]*s,"top":base-b[3]*s,"bot":base-b[1]*s})
    else:
        g.draw(TransformPen(pen,(s,0,0,-s,x,base)))
        out.append({"ch":ch,"d":pen.getCommands(),"x0":x+b[0]*s,"x1":x+b[2]*s,"top":base-b[3]*s,"bot":base-b[1]*s})
    x+=hm[gn][0]*s+SP
json.dump({"letters":out,"em":EM},open(sys.argv[2],"w"))
for o in out: print(o["ch"], round(o["x0"]), round(o["x1"]), round(o["top"]), round(o["bot"]))
