import numpy as np
import cv2
import math
from datetime import datetime
from PIL import Image, ImageEnhance





def timeit(method):
    def timed(*args, **kw):
        ts = datetime.now()
        result = method(*args, **kw)
        te = datetime.now()
        if 'log_time' in kw:
            dt = te-ts
            ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
            kw['log_time']['time_elapsed'] += ms
        else:
            print ('%r  %2.2f ms'  (method.__name__, (te - ts) * 1000))
        return result
    return timed


@timeit
def contains_pixel(new_pixel, lines_list,**kwargs):
    for line in lines_list:
        for pixel in line:
            if new_pixel[0] == pixel[0] and new_pixel[1] == pixel[1]:
                return True
    return False

def compute_slope (x1,x2,y1,y2):
    if x1-x2 == 0:
        return None
    return (y2-y1)/(x2-x1)

def compute_x_position_for_circle(h,k,r,y):
    eq = (r*r) - ((y-k)*(y-k))
    eq_sqrt = math.sqrt(eq)
    x_pos = int(eq_sqrt+h)
    return x_pos

@timeit
def get_line_coordinates(image_arr,h,k,r,black_shade=200,**kwargs):
    ''' (x-h)^2 + (y-k)^2 = r^2  '''
    image_height = len(image_arr)
    image_width = len(image_arr[0])
    coordinates =[]
    for i in range (k-r, k+r):
        if h+r > image_width or i<0 or i > image_height:
            continue
        x = compute_x_position_for_circle(h, k, r, i)
        if x >= image_width or i >= image_height:
            continue
        if image_arr[i][x] < black_shade:
            coordinates.append([x,i])
    return coordinates


def is_good_pixel(x, slope, intercept, image_array,black_shade=200):
    if slope is None:
        y = intercept
    else:
        y = int(intercept + (slope * x))
    if y > 0 and y <=len(image_array):
        if image_array[y][x] <= black_shade:
            return y
    return None




def line_detetction(color_map_array,image_arr,min_line_length_in_pixel=100,black_shade=200, pixel_error_tolerance=2):
    image_width = len(image_arr[0])
    image_height = len(image_arr)
    detected_lines = []

    time_taken_by_get_line_coordinates = {'time_elapsed':0}
    time_taken_by_contains_pixel = {'time_elapsed':0}

    x_hz = -1
    y_hz = -1

    total_pixels = sum(len(h_list) for h_list in colored_pixel_map)
    scanned_pixels = 0

    for h_slice in color_map_array:
        for pixel_coordinates in h_slice:
            x = pixel_coordinates[0]
            y = pixel_coordinates[1]
            scanned_pixels += 1
            i = (scanned_pixels / total_pixels) * 100
            print('\rdetection progress : ' + str(i),end="")
            '''skip horizontal pixels that are already accounted for'''
            if x_hz is not None and y_hz is not None and x <= x_hz and y == y_hz:
                continue

            possible_line_coordinates = get_line_coordinates(image_arr,x,y,min_line_length_in_pixel,black_shade,log_time=time_taken_by_get_line_coordinates)

            for coordinates in possible_line_coordinates:
                c_x = coordinates[0]
                c_y = coordinates[1]
                possible_line = []
                slope = compute_slope(x,c_x,y,c_y)
                previous_pointer = 0
                if slope is None:
                    previous_pointer = y
                    for scanner in range(y,image_height):
                        if image_arr[scanner][x] <= black_shade and scanner - previous_pointer -1 < pixel_error_tolerance:
                            possible_line.append([x,scanner])
                            previous_pointer = scanner
                        elif len(possible_line) >= min_line_length_in_pixel:
                            detected_lines.append(possible_line[:])
                            possible_line.clear()
                            break
                        else:
                            possible_line.clear()
                            break
                else:
                    intercept = c_y - (slope * c_x)
                    previous_pointer = x
                    for scanner in range(x , image_width):
                        y_of_x = is_good_pixel(scanner, slope, intercept,image_arr, black_shade)
                        x_hz = scanner
                        y_hz = y_of_x
                        if y_of_x is not None and scanner - previous_pointer -1 < pixel_error_tolerance:
                            possible_line.append([scanner, y_of_x])
                            previous_pointer = scanner
                        elif len(possible_line) >= min_line_length_in_pixel:
                            detected_lines.append(possible_line[:])
                            possible_line.clear()
                            break
                        else:
                            possible_line.clear()
                            break
    return detected_lines





def get_line_size_in_pixel_for_A4_image(image, line_size_in_mm):
    a4_width = 210
    image_width_in_pixel = image.width
    return ( image_width_in_pixel / a4_width ) *line_size_in_mm



def covert_pixels_array_to_image(pixel_array):
    return Image.fromarray(pixel_array)


def save_image_w_lines(iproc_obj):
    img_lines = iproc_obj.draw_lines(orig_img_as_background=True)
    img_lines_file = '2_1.png'
    cv2.imwrite(img_lines_file, img_lines)

def increase_contrast(image_name):
    image = Image.open(image_name)
    image = ImageEnhance.Contrast(image).enhance(5)
    image = ImageEnhance.Sharpness(image).enhance(2)
    return image

def image_to_array(image):
    im = image.convert('L')
    arr = np.fromiter(iter(im.getdata()), np.uint8)
    arr.resize(im.height, im.width)
    return arr

def fill_color_in_images_pixels(image_pixel_array, replcement_pixel_list, fill_color=255, return_image= False):
    for lines in replcement_pixel_list:
        for pixel in lines:
            image_pixel_array[pixel[1]][pixel[0]]=fill_color
    if return_image is True:
        return covert_pixels_array_to_image(image_pixel_array)
    return image_pixel_array


def detect_horizontal_line(horinatl_slice, min_line_length_in_pixel=10,pixel_error_tolearnce=3):
    if len(horinatl_slice) < min_line_length_in_pixel:
        return None
    anchor_pixel_pos = 0
    line_segments = []
    line = []
    for pixel_pos in horinatl_slice:
        if anchor_pixel_pos == 0:
            anchor_pixel_pos = pixel_pos[0] - 1
        if pixel_pos[0] - anchor_pixel_pos - 1 < pixel_error_tolearnce:
            line.append(pixel_pos)
        elif len(line) >= min_line_length_in_pixel:
            line_segments.append(line[:])
            line.clear()
        else:
            line.clear()
            line.append(pixel_pos)
        anchor_pixel_pos = pixel_pos[0]
    return line_segments if len(line_segments) > 0 else None



def detect_lines(colored_pixel_list, min_line_length_in_pixel=10, pixel_error_tolearnce=3):
    lines = []
    for h_slice in colored_pixel_list:
        horizontal_line = detect_horizontal_line(h_slice,min_line_length_in_pixel,pixel_error_tolearnce)
        if horizontal_line is not None:
            lines.extend(horizontal_line)
    return lines



def get_pixel_coordinate_map_for_staright_lines(image_pixel_array, black_shade=200):
    image_lines = []
    for h, h_slice in enumerate(image_pixel_array):
        line = []
        for v , pixel in enumerate(h_slice):
            if pixel < black_shade:
                line.append([v,h])
        if len(line) > 0:
            image_lines.append(line[:])
            line.clear()
    return image_lines


source_img = '2.png'
interim_img ='2_1.png'
final_img = '2_2.png'


data = image_to_array(increase_contrast(source_img))

colored_pixel_map = get_pixel_coordinate_map_for_staright_lines(data, black_shade = 200)
angled_lines = line_detetction(colored_pixel_map,data,min_line_length_in_pixel=30,black_shade=200,pixel_error_tolerance=5)


clean_img = fill_color_in_images_pixels(data,angled_lines,255,True)

clean_img.show()



