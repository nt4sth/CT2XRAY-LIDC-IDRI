# ------------------------------------------------------------------------------
# Copyright (c) Tencent
# Licensed under the GPLv3 License.
# Created by Kai Ma (makai0324@gmail.com)
# ------------------------------------------------------------------------------
import re
import os
import cv2
# import pfm
import time
import numpy as np
import matplotlib.pyplot as plt
from subprocess import check_output as qx
from ctxray_utils import load_scan_mhda, save_scan_mhda
from loguru import logger


# compute xray source center in world coordinate
def get_center(origin, size, spacing):
    origin = np.array(origin)
    size = np.array(size)
    spacing = np.array(spacing)
    center = origin + (size - 1) / 2 * spacing
    return center

# convert a ndarray to string
def array2string(ndarray):
    ret = ""
    for i in ndarray:
        ret = ret + str(i) + " "
    return ret[:-2]

def readPFM(file):
    file = open(file, 'rb')
    color = None
    width = None
    height = None
    scale = None
    endian = None

    header = file.readline().rstrip()
    if header.decode("ascii") == 'PF':
        color = True
    elif header.decode("ascii") == 'Pf':
        color = False
    else:
        raise Exception('Not a PFM file.')

    dim_match = re.match(r'^(\d+)\s(\d+)\s$', file.readline().decode("ascii"))
    if dim_match:
        width, height = list(map(int, dim_match.groups()))
    else:
        raise Exception('Malformed PFM header.')

    scale = float(file.readline().decode("ascii").rstrip())
    if scale < 0:  # little-endian
        endian = '<'
        scale = -scale
    else:
        endian = '>'  # big-endian

    data = np.fromfile(file, endian + 'f')
    shape = (height, width, 3) if color else (height, width)

    data = np.reshape(data, shape)
    data = np.flipud(data)
    return data, scale

# save a .pfm file as a .png file
def savepng(filename, direction):
    raw_data , scale = readPFM(filename)
    max_value = raw_data.max()
    im = (raw_data / (max_value+1e-5)  * 255).astype(np.uint8)
    # PA view should do additional left-right flip
    if direction == 1:
        im = np.fliplr(im)
    
    savedir, _ = os.path.split(filename)
    outfile = os.path.join(savedir, "xray{}.png".format(direction))
    plt.imsave(outfile, im, cmap=plt.cm.gray)
    image = cv2.imread(outfile)
    gray = cv2.split(image)[0]
    cv2.imwrite(outfile, gray)


if __name__ == '__main__':
    logger.add("file_{time}.log")
    root_path = './data/Test-LIDC-IDRI/'
    save_root_path = './data/Test-LIDC-IDRI'
    plasti_path = r'C:\Program Files\Plastimatch\bin'

    if not os.path.exists(save_root_path):
        os.makedirs(save_root_path)
    
    files_list = os.listdir(root_path)
    start = time.time()
    for fileIndex, fileName in enumerate(files_list):
        try:
            t0 = time.time()
            logger.info('Begin {}/{}: {}'.format(fileIndex+1, len(files_list), fileName))
            saveDir = os.path.join(root_path, fileName)
            if not os.path.exists(saveDir):
                os.makedirs(saveDir)
            # savePath is the .mha file store location
            savePath = os.path.join(saveDir, '{}.mha'.format(fileName))
            ct_itk, ct_scan, ori_origin, ori_size, ori_spacing = load_scan_mhda(savePath)
            # compute isocenter
            center = get_center(ori_origin, ori_size, ori_spacing)
            # map the .mha file value to (-1000, 1000)
            cmd_str = plasti_path + '/plastimatch adjust --input {} --output {}\
                    --pw-linear "0, -1000"'.format(savePath, saveDir+'/out.mha') 
            try:
                output = qx(cmd_str)
            except:
                logger.info("Error!")
                continue

            # get virtual xray file
            directions = [1, 2]
            for i in directions:
                if i == 1:
                    nrm = "0 1 0"
                else:
                    nrm = "1 0 0"    
                '''
                plastimatch usage
                -t : save format
                -g : sid sad [DistanceSourceToPatient]:541 
                            [DistanceSourceToDetector]:949.075012
                -r : output image resolution
                -o : isocenter position
                -z : physical size of imager
                -I : input file in .mha format
                -O : output prefix
                '''
                cmd_str = plasti_path + '/plastimatch drr -t pfm -n "{}" -S "541 949" \
                        -r "320 320" -o "{}" -z "500 500" -I {} -O {}'.format\
                        (nrm, array2string(center), saveDir+'/out.mha', saveDir+'/{}'.format(i))
                output = qx(cmd_str)
                # plastimatch would add a 0000 suffix 
                pfmFile = saveDir+'/{}'.format(i) + '0000.pfm'
                savepng(pfmFile, i)
            # remove the temp .mha file couse it is so large
            os.remove(saveDir+'/out.mha')
            t1 = time.time()
            logger.info('End! Case time: {}'.format(t1-t0))
        except:
            print("An error has occured.")
            continue
    end = time.time()
    logger.info('Finally! Total time: {}'.format(end-start))
