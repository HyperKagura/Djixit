import argparse
from PIL import Image


example_text = '''example:

python ../cut-images.py -H 4 -W 6 -f img.jpg -s 25 -p ../result/img_

this will produce files img_25.jpg, img_25.jpg,.. img_48.jpg

'''

parser = argparse.ArgumentParser(
    description="deploy-sagemaker",
    epilog=example_text,
    formatter_class=argparse.RawDescriptionHelpFormatter
)

requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument("-H", type=int, help="height - number of images", required=True)
requiredNamed.add_argument("-W", type=int, help="width - number of images", required=True)
requiredNamed.add_argument("-f", help="input image file", required=True)
requiredNamed.add_argument("-p", help="save path prefix", required=True)

parser.add_argument("-s", type=int, default=1, help="start number to save files")

args = parser.parse_args()

img = Image.open(args.f)
w, h = img.size
card_height = h / args.H
card_width = w / args.W
for i in range(0, args.W):
    for j in range(0, args.H):
        img.crop((i * card_width, j * card_height, (i+1) * card_width, (j+1) * card_height)).save(args.p + str(i * args.H + j + args.s) + ".jpg")
