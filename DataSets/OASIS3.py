import SimpleITK as sitk
import os, re
from glob import glob
from DataSets.DataLoader import DataSet

class OASIS3(DataSet):
    def __init__(self):
        path = "/data/johann/oasis3/OAS3*MR_*/anat*/NIFTI/*.nii.gz"
        path = "/mnt/hdd1/oasis1/out/OAS3*MR_*/anat*/NIFTI/*.nii.gz"
        subjects = list(glob(path))

        def subjectProperties(subj):
            props = {}
            pattern = re.compile(r'OAS3[^_]*_MR_d(?P<id>[0-9]+)/anat(?P<anat>[0-9]+)')
            oasis_id,anat_id = pattern.findall(subj_root)[0]

            props['id'] = "{}-{}".format(str(oasis_id),str(anat_id))
            props['img'] = subj
            return props

        self.props = sorted([subjectProperties(sb) for sb in subjects], key=lambda obj: obj['id'])

    def getFilePaths(self):
        return [p['img'] for p in self.props]

    def getFileIDs(self):
        return [p['id'] for p in self.props]

    def getDataSetPrefix(self):
        return "OASIS3"

    def loadVol(self, path_file):
        return sitk.ReadImage(path_file)

    def alignToAtlas(self, vol, atlas):
        vol.SetOrigin(atlas.GetOrigin())
        vol.SetDirection(atlas.GetDirection())
        return vol