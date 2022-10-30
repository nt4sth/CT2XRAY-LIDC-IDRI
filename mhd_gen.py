import os
import re
import pydicom
import numpy as np
import SimpleITK

from get_mask import mask
from tqdm import tqdm


if __name__ == '__main__':
    RootPathDicom = "./data/LIDC-IDRI"
    SaveRawData = "./data/Raw-LIDC-IDRI/" 
    SaveMaskData = "./data/Mask-LIDC-IDRI/"

    lstPath = [SaveRawData, SaveMaskData]
    for path in lstPath:
        if not os.path.exists(path):
            os.makedirs(path)
    
    for dir in tqdm(os.listdir(RootPathDicom)):
        for root, _, files in os.walk(os.path.join(RootPathDicom, dir)):
            lstFilesDCM = [os.path.join(root, file) for file in files \
                if file.endswith(".dcm")]
            if len(lstFilesDCM) >= 30:
                # try:
                  lstFilesDCM.sort()
                  # parse path
                  prefix = re.search(r'(?<=LIDC-IDRI\\).*$', root)[0].replace("\\", "_")
                  raw_file = os.path.join(SaveRawData, prefix+".mhd")
                  mask_file = os.path.join(SaveMaskData, prefix+"_outMultiLabelMask.mhd")

                  # load first dicom file as reference
                  RefDs = pydicom.read_file(lstFilesDCM[0])
                  # shape of image
                  ConstPixelDims = (int(RefDs.Rows), int(RefDs.Columns), len(lstFilesDCM))
                  # spacing information
                  ConstPixelSpacing = (float(RefDs.PixelSpacing[0]), float(RefDs.PixelSpacing[1]), float(RefDs.SliceThickness))
                  # origin
                  Origin = RefDs.ImagePositionPatient
          
                  ArrayDicom = np.zeros(ConstPixelDims, dtype=RefDs.pixel_array.dtype)
                  ArrayMask = np.zeros(ConstPixelDims, dtype=RefDs.pixel_array.dtype)

                  for filenameDCM in lstFilesDCM:
                      ds = pydicom.read_file(filenameDCM)
                      ct_array = ds.pixel_array
                      ArrayDicom[:, :, lstFilesDCM.index(filenameDCM)] = ct_array
                      ArrayMask[:, :, lstFilesDCM.index(filenameDCM)] = mask(ct_array.astype("uint8"))
                      
                  ArrayDicom = np.transpose(ArrayDicom, (2, 1, 0))
                  ArrayMask = np.transpose(ArrayMask, (2, 1, 0))

                  sitk_img = SimpleITK.GetImageFromArray(ArrayDicom, isVector=False)
                  sitk_img.SetSpacing(ConstPixelSpacing)
                  sitk_img.SetOrigin(Origin)
                  SimpleITK.WriteImage(sitk_img, os.path.join(SaveRawData, prefix+".mhd"))

                  mask_img = SimpleITK.GetImageFromArray(ArrayMask, isVector=False)
                  mask_img.SetSpacing(ConstPixelSpacing)
                  mask_img.SetOrigin(Origin)
                  SimpleITK.WriteImage(mask_img, mask_file)

                
                #except:
                  #print("An error has occured.")
                  #continue
                
            
        
        
    