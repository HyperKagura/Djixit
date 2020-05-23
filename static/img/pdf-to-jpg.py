from pdf2image import convert_from_path
import argparse


example_text = '''example:

python ../pdf-to-jpg.py -f cards.pdf -p ../result/img_

this will produce files img_1.jpg, img_2.jpg,.. for each page of input pdf

'''

parser = argparse.ArgumentParser(
    description="cut image on squares",
    epilog=example_text,
    formatter_class=argparse.RawDescriptionHelpFormatter
)

requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument("-f", help="input image file", required=True)
requiredNamed.add_argument("-p", help="save path prefix", required=True)

args = parser.parse_args()
pages = convert_from_path(args.f, 500)

for i, page in enumerate(pages):
    page.save(args.p + str(i+1) + ".jpg", 'JPEG')
