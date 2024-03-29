import cv2
import os, glob
import numpy as np
from hdr_utils import lum
import argparse


def direct_combine(sal_path_list):
    blank_img = np.zeros(cv2.imread(sal_path_list[0]).shape, dtype=np.float32)
    # print blank_img
    for sal_path in sal_path_list:
        blank_img += cv2.imread(sal_path).astype(np.float32)

    blank_img = blank_img/len(sal_path_list)
    return blank_img

def max_out(sal_path_list):
    blank_img = np.zeros(cv2.imread(sal_path_list[0],0).shape, dtype=np.float32)
    for sal_path in sal_path_list:
        blank_img = np.maximum(cv2.imread(sal_path,0).astype(np.float32), blank_img)

    return blank_img

def sum_product(sal_path_list):
    sum_img = np.zeros(cv2.imread(sal_path_list[0],0).shape, dtype=np.float32)
    product_img = np.ones(cv2.imread(sal_path_list[0],0).shape, dtype=np.float32)
    for sal_path in sal_path_list:
        sal_map = cv2.imread(sal_path, 0).astype(np.float32)
        sum_img = sum_img + sal_map
        product_img = np.multiply(product_img, np.add(sal_map,1))

    sum_img = sum_img/len(sal_path_list)
    final_map = np.add(sum_img, product_img)
    
    ## normalization
    final_map = final_map-final_map.min()
    final_map = final_map/final_map.max()
    final_map = final_map*255
    return final_map

def minkowski(sal_path_list):
    m = 3.5
    sum_img = np.zeros(cv2.imread(sal_path_list[0],0).shape, dtype=np.float32)
    
    for sal_path in sal_path_list:
        sal_map = cv2.imread(sal_path, 0).astype(np.float32)
        sum_img = sum_img + np.power(sal_map,m)
    sum_img = np.power(sum_img, 1/m)

    sum_img = sum_img-sum_img.min()
    sum_img = sum_img/sum_img.max()
    sum_img = sum_img*255
    return sum_img

def mysort(img_path):
    index = int(os.path.splitext(os.path.basename(img_path))[0].split('_')[-1])
    return index

def global_contrast_weighted_combine(prefix, sal_path_list, exposion_img_path_list):
    exposion_img_path_list = exposion_img_path_list[:len(sal_path_list)]
    assert(len(sal_path_list)==len(exposion_img_path_list))
    sal_path_list.sort(key=mysort)
    exposion_img_path_list.sort(key=mysort)

    ## estimate contrast
    contrast_list = []
    for exposion_img_path in exposion_img_path_list:
        print exposion_img_path
        luminance_map = lum(cv2.imread(exposion_img_path)[:, :, ::-1])
        contrast_list.append(np.std(luminance_map)/np.mean(luminance_map))


    ## weighted fusion
    blank_img = np.zeros(cv2.imread(sal_path_list[0], 0).shape, dtype=np.float32)
    for (sal_path,weight) in zip(sal_path_list,contrast_list):
        sal = cv2.imread(sal_path, 0)
        blank_img += weight * sal

    return blank_img

from matplotlib import pyplot as plt
def plot_global_contrast_weight(prefix, sal_path_list, exposion_img_path_list):
    exposion_img_path_list = exposion_img_path_list[:len(sal_path_list)]
    assert(len(sal_path_list)==len(exposion_img_path_list))
    sal_path_list.sort(key=mysort)
    exposion_img_path_list.sort(key=mysort)

    ## estimate contrast
    contrast_list = []
    for exposion_img_path in exposion_img_path_list:
        print exposion_img_path
        luminance_map = lum(cv2.imread(exposion_img_path)[:, :, ::-1])
        contrast_list.append(np.std(luminance_map)/np.mean(luminance_map))
    plt.plot([i for i in range(len(contrast_list))], contrast_list)
    # plt.show()
    output_name = prefix+'.png'
    plt.savefig(output_name)

# def local_contrast_weighted_combine(prefix, sal_path_list, exposion_img_path_list, patch_size=(80,80), downsize=(800,800)):
#     for i in range()

if __name__ =='__main__':

    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=str,required=True)
    parser.add_argument('--model',type=str,required=True)
    parser.add_argument('--method',type=str,required=True)
    args = parser.parse_args()


    # folder='SAM'
    # fusion_mode='AVG'
    dataset = args.dataset
    folder = args.model
    fusion_mode = args.method


    if dataset =='hdreye':
        img_dir='/data/SaliencyDataset/Image/HDREYE/images/HDR'
        exposion_dir='/data/SaliencyDataset/Image/HDREYE/images/exposure_stack'
        sal_dir='/data/SaliencyDataset/Image/HDREYE/saliency_map/exposure_stack/%s'%folder
        output_dir='/data/SaliencyDataset/Image/HDREYE/saliency_map/fusion/%s-fusion-%s'%(fusion_mode,folder)
    if dataset =='ethyma':
        img_dir='/data/SaliencyDataset/Image/ETHyma/images'
        exposion_dir='/data/SaliencyDataset/Image/ETHyma/exposure_stack'
        sal_dir='/data/SaliencyDataset/Image/ETHyma/saliency_map/exposure_stack/%s'%folder
        output_dir='/data/SaliencyDataset/Image/ETHyma/saliency_map/fusion/%s-fusion-%s'%(fusion_mode,folder)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    image_name_list = os.listdir(img_dir)
    sal_path_list = glob.glob(os.path.join(sal_dir, '*.*'))
    exposion_path_list = glob.glob(os.path.join(exposion_dir, '*.*'))



    for image_name in image_name_list:
        prefix=os.path.splitext(image_name)[0]
        cur_sal_path_list = [path for path in sal_path_list if prefix in path]
        cur_exposion_path_list = [path for path in exposion_path_list if prefix in path]

        # blank_img = np.zeros(cv2.imread(cur_sal_path_list[0]).shape, dtype=np.float32)
        # # print blank_img
        # for sal_path in cur_sal_path_list:
        #     blank_img += cv2.imread(sal_path).astype(np.float32)

        # blank_img = blank_img/len(cur_sal_path_list)
        print cur_sal_path_list,cur_exposion_path_list
        if fusion_mode=='AVG':
            fusion_img = direct_combine(cur_sal_path_list)
        elif fusion_mode=='MAX':
            fusion_img = max_out(cur_sal_path_list)
        elif fusion_mode=='SP':
            fusion_img = sum_product(cur_sal_path_list)   
        elif fusion_mode=='MINKOWSKI':
            fusion_img = minkowski(cur_sal_path_list)  
        elif fusion_mode=='GCW':
            fusion_img = global_contrast_weighted_combine(prefix, cur_sal_path_list, cur_exposion_path_list)
        elif fusion_mode=='GCW_PLOT':
            plot_global_contrast_weight(prefix, cur_sal_path_list, cur_exposion_path_list)
            continue
        elif fusion_mode=='LCW':
            fusion_img = global_contrast_weighted_combine(prefix, cur_sal_path_list, cur_exposion_path_list)
        else:
            raise NotImplementedError
        #normalization
        fusion_img = fusion_img - fusion_img.min()
        fusion_img = fusion_img / fusion_img.max()
        fusion_img = fusion_img * 255
        output_name = os.path.join(output_dir, prefix+'.png')

        cv2.imwrite(output_name, fusion_img)
        print output_name, 'saved.'
