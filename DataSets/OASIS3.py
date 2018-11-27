import SimpleITK as sitk
import os, re
from glob import glob
from DataSets.DataLoader import DataSet

class OASIS3(DataSet):
    def __init__(self):
        path = "/data/johann/oasis3/OAS3*MR_*/anat*/NIFTI/*.nii.gz"
        path = "/mnt/hdd1/oasis3/OAS3*MR_*/anat*/NIFTI/*.nii.gz"
        subjects = list(glob(path))

        def subjectProperties(subj):
            props = {}
            pattern = re.compile(r'OAS3(?P<id1>[0-9]+)_MR_d(?P<id2>[0-9]+)/anat(?P<anat>[0-9]+)')
            oasis_id1,oasis_id2,anat_id = pattern.findall(subj)[0]

            props['id'] = "{}-{}-{}".format(str(oasis_id1),str(oasis_id2),str(anat_id))
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
