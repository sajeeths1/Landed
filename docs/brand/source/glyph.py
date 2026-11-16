import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
f=TTFont(sys.argv[1]); gs=f.getGlyphSet(); g=gs[f.getBestCmap()[ord('L')]]
bp=BoundsPen(gs); g.draw(bp); x0,y0,x1,y1=bp.bounds
H=236.0; s=H/(y1-y0); left=190.0; bottom=372.0
K=float(sys.argv[2])          # horizontal stretch of the foot
XS=left+(442-x0)*s            # right edge of the stem (font x=442)
class MapPen:
    def __init__(self,o): self.o=o
    def m(self,p): return None if p is None else ((XS+(p[0]-XS)*K if p[0]>XS else p[0]), p[1])
    def moveTo(self,p): self.o.moveTo(self.m(p))
    def lineTo(self,p): self.o.lineTo(self.m(p))
    def qCurveTo(self,*ps): self.o.qCurveTo(*[self.m(p) for p in ps])
    def curveTo(self,*ps): self.o.curveTo(*[self.m(p) for p in ps])
    def closePath(self): self.o.closePath()
    def endPath(self): self.o.endPath()
pen=SVGPathPen(gs, ntos=lambda v: ('%.1f'%v).rstrip('0').rstrip('.'))
g.draw(TransformPen(MapPen(pen),(s,0,0,-s,left-x0*s,bottom+y0*s)))
print(pen.getCommands())
