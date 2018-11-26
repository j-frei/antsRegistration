import numpy as np
import SimpleITK as sitk
import os
from ants.antsRegistration import registerImage
from DataSets.OASIS1 import OASIS1
from DataSets.OASIS3 import OASIS3

def resampleImage(img, atlas, trf=None):
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(atlas)
    resampler.SetOutputSpacing(atlas.GetSpacing())
    resampler.SetSize(atlas.GetSize())
    if trf:
        resampler.SetTransform(trf)
    return resampler.Execute(img)

def prepareDatasets():
    atlas = sitk.ReadImage(os.path.join(os.path.dirname(__file__), "atlas", "atlas.nii.gz"))
    #storage_folder = "/data/johann/datasets_prepared"
    storage_folder = "/mnt/hdd1/datasets_prepared"
    datasets = [OASIS1,OASIS3]

    for ds in datasets:
        current_dataset = ds()
        print("Reading dataset: {}".format(current_dataset.getDataSetPrefix()))
        for v_path, v_id in zip(current_dataset.getFilePaths(), current_dataset.getFileIDs()):
            # storage_id
            storage_id = "{}_{}".format(current_dataset.getDataSetPrefix(), v_id)
            storage_path = os.path.join(storage_folder, storage_id + ".nii.gz")

            if not os.path.exists(storage_path):
                # load volume
                vol_loaded = current_dataset.loadVol(v_path)
                # apply dataset-specific modifications
                vol_aligned = current_dataset.alignToAtlas(vol_loaded, atlas)
                # resample along atlas
                vol_resampled = resampleImage(vol_aligned, atlas)

                out = registerImage(vol_resampled, atlas, speed="better")
                # keys: out["transforms_out"] -> [path to trfs]
                # keys: out["warpedMovingVolume"] -> [path to warpedVol]
                # get transform mov->fix [0], not fix->mov [1]
                movToFix = sitk.ReadTransform(out['transforms_out'][0])
                # resample again
                final_img = resampleImage(vol_aligned, atlas, movToFix)

                sitk.WriteImage(final_img, storage_path)

                print("Successfully preprocessed: {}".format(storage_id))
            else:
                print("Skipping existing file: {}".format(storage_id))

    print("Done!")


if __name__ == "__main__":
    prepareDatasets()
