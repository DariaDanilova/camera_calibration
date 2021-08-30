import numpy
import cv2

import math
import copy
import itertools

from scipy import ndimage


class Corners(object):

    def find_chessboard_coordinates(self, image_path):

        ###GFTT

        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

        corners = cv2.goodFeaturesToTrack(gray,1500,0.001,10)
        corners = numpy.int0(corners)

        corners = corners.reshape(corners.shape[0], corners.shape[2]).tolist()
        corners = [tuple(el) for el in corners]

        ###ПЕРВИЧНАЯ ФИЛЬТРАЦИЯ

        #рассчитать корреляцию между исходным и новым квадратом, где A и B - две матрицы размером nxn, n=d_ij
        def find_CorrAB(A, B):
            meanA = A.mean()
            meanB = B.mean()
            CorrAB = numpy.sum(numpy.sum((A-meanA).dot(B-meanB),axis=0))/numpy.sum(numpy.sum(numpy.square(A-meanA),axis=0))*numpy.sum(numpy.sum(numpy.square(B-meanB),axis=0))**0.5
            return CorrAB

        def binarize_image(img):
            ret, threshold_image = cv2.threshold(img, img.mean(), 1, 0)
            return threshold_image

        def find_end_points(binarized_img):
            upper_side = binarized_img[0] #верхняя граница квадрата
            right_side = binarized_img[:,-1] #правая граница квадрата
            lower_side = binarized_img[-1]
            left_side = binarized_img[:,0]

            #объединяем в один массив
            all_sides = numpy.concatenate((upper_side, right_side, numpy.flip(lower_side, 0), numpy.flip(left_side, 0)), axis=None)

            #считаем кол-во end points
            count_end_points = 0
            neighboring_pixel = all_sides[0]
            for i in range(1, len(all_sides)):
                if all_sides[i] != neighboring_pixel:
                    count_end_points += 1
                neighboring_pixel = all_sides[i]
            return count_end_points


        #три квадрата с n=11, 23 и 35

        n=[11, 23, 35]
        corners_with_4_end_points = []
        for corner in corners:
            sub_images = []
            for size in n:
                half_size = round(size//2)
                nn_square = numpy.array(gray[(corner[1]-half_size):(corner[1]+half_size+1),(corner[0]-half_size):(corner[0]+half_size+1)])
                if nn_square.shape!=(0,0) and nn_square.shape[0]==nn_square.shape[1]:
                    sub_images.append(nn_square)
                #преобразуем в двоичное изображение
                if len(sub_images) == 3:
                    for sub_im in sub_images:
                        binarized_img = binarize_image(sub_im)
                        #сканируем границы квадрата для поиска end points
                        end_points = find_end_points(binarized_img)
                    if end_points == 4:
                        #if (binarized_img.shape==(11,11) and 0<=find_CorrAB(chessboard_corner11, binarized_img) <= corr_threshold) or (binarized_img.shape==(23,23) and 0<=find_CorrAB(chessboard_corner23, binarized_img) <= corr_threshold) or (binarized_img.shape==(35,35) and 0<=find_CorrAB(chessboard_corner35, binarized_img) <= corr_threshold):
                        corners_with_4_end_points.append(corner)

        #удалить дубли
        corners_with_4_end_points = list(set(corners_with_4_end_points))

        ### ВЫЧИСЛИТЬ self-correlation, ПОСТРОИТЬ КАРТУ self-correlation

        cs = 1

        a = numpy.array([[0, 255],
                         [255,0]])
        c = numpy.array([[64,64,0],
                         [0,64,64]])

        def find_Corrm(corr):
            corrm = math.exp(corr/0.8-1)
            return corrm

        #выберем квадрат mxm с центром в каждом пикселе в угловой окрестности kxk
        m = 2*cs

        mm_squares = {}
        for corner in corners_with_4_end_points:
            mm_square = numpy.array(gray[(corner[1]-m):(corner[1]+m+1),(corner[0]-m):(corner[0]+m+1)].tolist())
            if mm_square.shape!=(0,) and mm_square.shape[0]==mm_square.shape[1]:
                #вычислить стандартное отклонение для квадрата
                gray_square = cv2.cvtColor(numpy.float32(mm_square), cv2.COLOR_BGRA2RGBA)
                mean, std = cv2.meanStdDev(gray_square)
                if ndimage.standard_deviation(c)/2<ndimage.standard_deviation(gray_square)<=ndimage.standard_deviation(a):   
                    mm_squares[tuple(corner)] = [mm_square]


        #повернуть на 180 градусов матрицы
        for keyvalue in mm_squares.items():
            key, value = keyvalue[0], keyvalue[1]
            value.append(numpy.rot90(value[0],2))

        #вычислим корреляцию и увеличим самокорреляцию
        for mm in mm_squares.items():
            key, value = mm[0], mm[1]
            try:
                value.append(find_Corrm(find_CorrAB(value[0], value[1])))
            except OverflowError:
                value.append(1.7976931348623157e+308) #максимальное значение float

        #self-correlation map, где 0 присвоены пикселям за пределами квадратов mxm
        self_corr_map = numpy.zeros_like(gray)

        for keyvalues in mm_squares.items():
            key, value = keyvalues[0], keyvalues[1]
            self_corr_map[(key[1]-m):(key[1]+m+1),(key[0]-m):(key[0]+m+1)] = value[0]

        #пиксели за пределами угловой окрестности станут 0
        for keyvalues in mm_squares.items():
            key, values = keyvalues[0], keyvalues[1]

            mm_matrix = copy.deepcopy(keyvalues[1][0])
            mm_matrix[0:cs]=0 #верхние строки
            mm_matrix[-cs:,:]=0 #нижние строки
            mm_matrix[:,0:cs]=0 #правая сторона
            mm_matrix[:,-cs:]=0 #левая сторона
            keyvalues[1].append(mm_matrix)

        #делаем замену
        for keyvalues in mm_squares.items():
            key, value = keyvalues[0], keyvalues[1][3]
            self_corr_map[(key[1]-m):(key[1]+m+1),(key[0]-m):(key[0]+m+1)] = value

        #использовать для пункта удалить выбросы
        self_corr_corners = []
        for keyvalues in mm_squares.items():
            key = keyvalues[0]
            self_corr_corners.append(key)

        ###NMS

        def nms(img, n):

            MaximumAt = []
            sze = 2*n+1

            width, height = img.shape

            #разбить входное изображение наблоки
            for i in range(n, width-n, sze):
                for j in range(n, height-n, sze):
                    arrmij = []
                    arrmij2 = []
                    arrx = []
                    arry = []

                    # найти в каждом блоке наибольший элемент, который является единственным возможным локальным максимумом
                    mi, mj = i, j
                    for i2 in range(i, i + n, 1):
                        for j2 in range(j, j + n, 1):
                            if(img[i2, j2] > img[mi, mj]):
                                mi, mj = i2, j2

                    #проверить полное окружение этого кандидата, при этом элементы самого блока м.б. пропущены, т.к. они
                    #по конструкции уже меньше кандидата

                    flag_found = False

                    #полное окружение
                    for k1 in range(mi - n, mi + n, 1):
                        for k2 in range(mj - n, mj + n, 1):
                            arrmij.append((k1, k2))

                    #элементы самого блока    
                    for k1 in range(i, i + n, 1):
                        for k2 in range(j, j + n, 1):
                            arrmij2.append((k1, k2))

                    #вычитание
                    arr_substraction = [item for item in arrmij if item not in arrmij2] 

                    for ind in arr_substraction:
                        x, y = ind[0], ind[1]
                        arrx.append(x)
                        arry.append(y)

                    for i2 in range(len(arrx)):
                        for j2 in range(len(arry)):
                            if img[arrx[i2], arry[j2]] > img[mi, mj]:
                                flag_found = True
                                break

                    if (flag_found):
                        MaximumAt.append([mi, mj])
            return MaximumAt

        #MaximumAt = nms(self_corr_map, 7)

        ###УДАЛИТЬ ВЫБРОСЫ

        #вычислить расстояние между каждыми двумя углами и найти 12 ближайших для каждого угла
        def find_12_nearest_corners(arr_corners):
            twelve_dist_coner = {}
            for i in arr_corners:
                temp_dist_coner = {}
                for j in arr_corners:
                    temp_dist_coner[tuple(j)] = math.hypot(i[0] - j[0], i[1] - j[1])
                #сортировка словаря по значению
                sorted_dict = dict(sorted(temp_dist_coner.items(), key=lambda item: item[1]))
                twelve_dist_coner[tuple(i)] = list(sorted_dict.items())[1:13]
            return twelve_dist_coner 

        twelve_dist_coner = find_12_nearest_corners(corners_with_4_end_points)

        #найдем CorrRadius - половину длины стороны квадрата, где d_ij обозначает расстояние между углами C(i) и C(j)
        def find_CorrRadius(d_ij):
            max_d = d_ij/4 if d_ij/4 > 5 else 5
            CorrRadius = max_d if max_d < d_ij/2 else d_ij/2
            return CorrRadius

        def remove_outliers(i_corner):
            checkerboard_corners = []
            threshold = 0.5
            for keyvalue in i_corner.items():
                summ = 0
                key, value = keyvalue[0], keyvalue[1]
                value = [abs(el) for el in value]
                for el in value:
                    if el > threshold:
                        summ = summ + el
                if summ > 1:
                    checkerboard_corners.append(key)
            return checkerboard_corners

        #те i, что принадлежат CN(j)
        i_in_Cj = {}
        for keyvalue_i in twelve_dist_coner.items():
            temp_i_in_Cj=[]
            key_i, value_i = keyvalue_i[0], keyvalue_i[1]
            for keyvalue_j in twelve_dist_coner.items():
                #if key_i[0] != keyvalue_j[0][0] and key_i[1] != keyvalue_j[0][1]:
                if keyvalue_i[0] != keyvalue_j[0]:              #####Проверить эти условия, вроде одинаковые, но дает разный результат
                    key_j, value_j = keyvalue_j[0], keyvalue_j[1]
                #для каждого угла из текущего вектора
                    for el in value_j:
                        if key_i[0] == el[0][0] and key_i[1] == el[0][1]:
                            temp_i_in_Cj.append(key_j)
                    if len(temp_i_in_Cj)!= 0:
                        i_in_Cj[tuple(key_i)] = temp_i_in_Cj

        neighbors = {}
        #для каждого j из i_in_Cj проверим принадлежат ли они CN(i)
        for el in i_in_Cj.items():
            key_i, j_from_values_i = el[0], el[1]
            temp_i_in_Cj_new = []
            #для каждого j из вектора CN(i)
            for j in j_from_values_i:
                for keyvalue_i in twelve_dist_coner.items():
                    key_12i, value_12i = keyvalue_i[0], keyvalue_i[1]
                    #для соответствующих i ищем
                    if key_i == key_12i:
                        #то проверяем список точек
                        for v_j in value_12i:
                        #проверяем есть ли здесь, в CN(i), j
                            if j[0] == v_j[0][0] and j[1] == v_j[0][1]:
                                temp_i_in_Cj_new.append((j, v_j[1]))
            if len(temp_i_in_Cj_new) != 0:
                neighbors[tuple(key_i)] = temp_i_in_Cj_new

        i_corner = {}

        for el in neighbors.items():
            i_corner_corr = []
            key_i, values = el[0], el[1]
            for v_j in values:
                #размер окрестности
                half_of_squre_side = round(find_CorrRadius(v_j[1]))
                A = numpy.array(gray[(key_i[1]-half_of_squre_side):(key_i[1]+half_of_squre_side+1),(key_i[0]-half_of_squre_side):(key_i[0]+half_of_squre_side+1)].tolist())
                B = numpy.array(gray[(v_j[0][1]-half_of_squre_side):(v_j[0][1]+half_of_squre_side+1),(v_j[0][0]-half_of_squre_side):(v_j[0][0]+half_of_squre_side+1)].tolist())
                #считаем корреляцию
                if (A.shape != (0,) and B.shape != (0,)) and (A.shape == B.shape) and (A.shape[0]==A.shape[1]):
                    Corr_ij = find_CorrAB(A, B)
                    i_corner_corr.append(Corr_ij)
            if len(i_corner_corr) != 0:
                i_corner[tuple(key_i)] = i_corner_corr

        checkerboard_corners = remove_outliers(i_corner)
        return checkerboard_corners

    def show_keypoints(self, image_path, keypoints_coordinates):
        img = cv2.imread(image_path)
        for i in keypoints_coordinates:
            x = i[1]
            y = i[0]
            cv2.circle(img,(y,x),10,(0, 255, 120),-1)

        img = cv2.resize(img, (500,400))
        cv2.imshow('corners',img)
        cv2.waitKey(0)

corners = Corners()
image_path = 'chessboard.png'
coordinates = sorted(corners.find_chessboard_coordinates(image_path))
#print(coordinates)
corners.show_keypoints(image_path, coordinates)