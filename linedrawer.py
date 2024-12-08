from random import *
import math
import os
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import cv2
# from filters import *
from util import distsum
import perlin
from strokesort import *
class ImageSketcher:
    def __init__(self, input_image_path="test.jpg", export_path="output/out.svg", 
                 bitmap_output="output/bitmap_output.png", draw_contours=True, 
                 draw_hatch=True, show_bitmap=True, resolution=1024, 
                 hatch_size=16, contour_simplify=2):
        self.input_image_path = input_image_path
        self.export_path = export_path
        self.bitmap_output = bitmap_output
        self.draw_contours = draw_contours
        self.draw_hatch = draw_hatch
        self.show_bitmap = show_bitmap
        self.resolution = resolution
        self.hatch_size = hatch_size
        self.contour_simplify = contour_simplify
        self.no_cv = False
        
        try:
            import numpy as np
            import cv2
        except ImportError:
            print("Cannot import numpy/openCV. Switching to NO_CV mode.")
            self.no_cv = True

    def find_edges(self, IM):
        print("Finding edges...")
        if self.no_cv:
            appmask(IM, [F_SobelX, F_SobelY])
        else:
            im = np.array(IM)
            im = cv2.GaussianBlur(im, (3, 3), 0)
            im = cv2.Canny(im, 100, 200)
            IM = Image.fromarray(im)
        return IM.point(lambda p: p > 128 and 255)  

    def getdots(self, IM):
        print("Getting contour points...")
        PX = IM.load()
        dots = []
        w, h = IM.size
        for y in range(h - 1):
            row = []
            for x in range(1, w):
                if PX[x, y] == 255:
                    if len(row) > 0:
                        if x - row[-1][0] == row[-1][-1] + 1:
                            row[-1] = (row[-1][0], row[-1][-1] + 1)
                        else:
                            row.append((x, 0))
                    else:
                        row.append((x, 0))
            dots.append(row)
        return dots

    def connectdots(self, dots):
        print("Connecting contour points...")
        contours = []
        for y in range(len(dots)):
            for x, v in dots[y]:
                if v > -1:
                    if y == 0:
                        contours.append([(x, y)])
                    else:
                        closest = -1
                        cdist = 100
                        for x0, v0 in dots[y - 1]:
                            if abs(x0 - x) < cdist:
                                cdist = abs(x0 - x)
                                closest = x0

                        if cdist > 3:
                            contours.append([(x, y)])
                        else:
                            found = 0
                            for i in range(len(contours)):
                                if contours[i][-1] == (closest, y - 1):
                                    contours[i].append((x, y,))
                                    found = 1
                                    break
                            if found == 0:
                                contours.append([(x, y)])
            for c in contours:
                if c[-1][1] < y - 1 and len(c) < 4:
                    contours.remove(c)
        return contours

    def getcontours(self, IM, sc=2):
        print("Generating contours...")
        IM = self.find_edges(IM)
        IM1 = IM.copy()
        IM2 = IM.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        dots1 = self.getdots(IM1)
        contours1 = self.connectdots(dots1)
        dots2 = self.getdots(IM2)
        contours2 = self.connectdots(dots2)

        for i in range(len(contours2)):
            contours2[i] = [(c[1], c[0]) for c in contours2[i]]    
        contours = contours1 + contours2

        for i in range(len(contours)):
            for j in range(len(contours)):
                if len(contours[i]) > 0 and len(contours[j]) > 0:
                    if distsum(contours[j][0], contours[i][-1]) < 8:
                        contours[i] = contours[i] + contours[j]
                        contours[j] = []

        for i in range(len(contours)):
            contours[i] = [contours[i][j] for j in range(0, len(contours[i]), 8)]

        contours = [c for c in contours if len(c) > 1]

        for i in range(0, len(contours)):
            contours[i] = [(v[0] * sc, v[1] * sc) for v in contours[i]]

        for i in range(0, len(contours)):
            for j in range(0, len(contours[i])):
                contours[i][j] = int(contours[i][j][0] + 10 * perlin.noise(i * 0.5, j * 0.1, 1)), int(contours[i][j][1] + 10 * perlin.noise(i * 0.5, j * 0.1, 2))

        return contours

    def hatch(self, IM, sc=16):
        print("Hatching...")
        PX = IM.load()
        w, h = IM.size
        lg1 = []
        lg2 = []
        for x0 in range(w):
            for y0 in range(h):
                x = x0 * sc
                y = y0 * sc
                if PX[x0, y0] > 144:
                    pass
                elif PX[x0, y0] > 64:
                    lg1.append([(x, y + sc / 4), (x + sc, y + sc / 4)])
                elif PX[x0, y0] > 16:
                    lg1.append([(x, y + sc / 4), (x + sc, y + sc / 4)])
                    lg2.append([(x + sc, y), (x, y + sc)])
                else:
                    lg1.append([(x, y + sc / 4), (x + sc, y + sc / 4)])
                    lg1.append([(x, y + sc / 2 + sc / 4), (x + sc, y + sc / 2 + sc / 4)])
                    lg2.append([(x + sc, y), (x, y + sc)])

        lines = [lg1, lg2]
        for k in range(0, len(lines)):
            for i in range(0, len(lines[k])):
                for j in range(0, len(lines[k])):
                    if lines[k][i] != [] and lines[k][j] != []:
                        if lines[k][i][-1] == lines[k][j][0]:
                            lines[k][i] = lines[k][i] + lines[k][j][1:]
                            lines[k][j] = []
            lines[k] = [l for l in lines[k] if len(l) > 0]
        lines = lines[0] + lines[1]

        for i in range(0, len(lines)):
            for j in range(0, len(lines[i])):
                lines[i][j] = int(lines[i][j][0] + sc * perlin.noise(i * 0.5, j * 0.1, 1)), int(lines[i][j][1] + sc * perlin.noise(i * 0.5, j * 0.1, 2)) - j
        return lines

    def sketch(self,IM):
        print("sketch")
        w, h = IM.size
        IM = IM.convert("L")
        IM = ImageOps.autocontrast(IM, 10)

        lines = []
        if self.draw_contours:
            lines += self.getcontours(IM.resize((self.resolution // self.contour_simplify, 
                                                  self.resolution // self.contour_simplify * h // w)), 
                                                self.contour_simplify)
        if self.draw_hatch:
            lines += self.hatch(IM.resize((self.resolution // self.hatch_size, 
                                            self.resolution // self.hatch_size * h // w)), 
                                        self.hatch_size)

        lines = sortlines(lines)
        # if self.show_bitmap:
            # self.show_bitmap_image(lines, w, h)

        self.save_svg(lines)

        print(len(lines), "strokes.")
        print("Done.")
        return lines

    def load_image(self):
        possible = [self.input_image_path, "./" + self.input_image_path, 
                    self.input_image_path + ".jpg", self.input_image_path + ".png", 
                    self.input_image_path + ".tif"]
        for p in possible:
            try:
                return Image.open(p)
            except FileNotFoundError:
                continue
        return None

    def show_bitmap_image(self, lines, w, h):
        disp = Image.new("RGB", (self.resolution, self.resolution * h // w), (255, 255, 255))
        draw = ImageDraw.Draw(disp)
        for l in lines:
            draw.line(l, (0, 0, 0), 5)
        disp.show()
        
        os.makedirs(os.path.dirname(self.bitmap_output), exist_ok=True)
        disp.save(self.bitmap_output)
        print(f"Bitmap line-drawing saved at: {self.bitmap_output}")

    def save_svg(self, lines):
        with open(self.export_path, 'w') as f:
            f.write(self.makesvg(lines))

    def makesvg(self, lines):
        print("Generating SVG file...")
        out = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">'
        for l in lines:
            l = ",".join([str(p[0] * 0.5) + "," + str(p[1] * 0.5) for p in l])
            out += '<polyline points="' + l + '" stroke="black" stroke-width="2" fill="none" />\n'
        out += '</svg>'
        return out

# Example usage:
if __name__ == "__main__":
    sketcher = ImageSketcher()
    sketcher.sketch()
