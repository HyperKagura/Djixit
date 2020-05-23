import argparse
from PIL import Image


example_text = '''example:

python ../cut-images.py -H 4 -W 6 -i img.jpg -s 25 -o ../result/img_

this will produce files img_25.jpg, img_25.jpg,.. img_48.jpg

'''

parser = argparse.ArgumentParser(
    description="cut image on squares",
    epilog=example_text,
    formatter_class=argparse.RawDescriptionHelpFormatter
)

requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument("-H", type=int, help="height - number of images", required=True)
requiredNamed.add_argument("-W", type=int, help="width - number of images", required=True)
requiredNamed.add_argument("-i", help="input image file", required=True)
requiredNamed.add_argument("-o", help="save path prefix", required=True)

parser.add_argument("-s", type=int, default=1, help="start number to save files")
requiredNamed.add_argument("-l", type=int, default=0, help="left margin in pixels")
requiredNamed.add_argument("-r", type=int, default=0, help="right margin in pixels")
requiredNamed.add_argument("-t", type=int, default=0, help="top margin in pixels")
requiredNamed.add_argument("-b", type=int, default=0, help="bottom margin in pixels")

requiredNamed.add_argument("-p", type=int, default=0, help="horizontal padding between cards in pixels")
requiredNamed.add_argument("-v", type=int, default=0, help="vertical padding between cards in pixels")

args = parser.parse_args()

img = Image.open(args.i)
w, h = img.size
w -= args.l
w -= args.r
h -= args.t
h -= args.b
card_height = int((h - (args.H - 1) * args.v) / args.H)
card_width = int((w - (args.W - 1) * args.p) / args.W)
for i in range(0, args.W):
    for j in range(0, args.H):
        x = args.l + args.p * i + i * card_width
        y = args.t + args.v * j + j * card_height
        img.crop((x, y, x + card_width, y + card_height)).save(args.o + str(i * args.H + j + args.s) + ".jpg")
