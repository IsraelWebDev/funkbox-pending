import sys
from PIL import Image, ImageChops
a=Image.open(sys.argv[1]).convert('L'); b=Image.open(sys.argv[2]).convert('L').resize(a.size)
# ref in red channel, candidate in green: misalignments show as red/green
im=Image.merge('RGB',(b,a,a.point(lambda v: v)))
box=tuple(int(v) for v in sys.argv[4].split(',')) if len(sys.argv)>4 else (0,0)+a.size
im.crop(box).save(sys.argv[3])
