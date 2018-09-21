import SimpleITK as sitk
import os, re
from glob import glob
from DataSets.DataLoader import DataSet

class OASIS1(DataSet):
    def __init__(self):
        path = "/data/johann/oasis1/OAS1_*_MR1"
        path = "/mnt/hdd1/oasis1/out/OAS1_*_MR1"
        subjects = list(glob(path))

        def subjectProperties(subj_root):
            props = {}
            pattern = re.compile(r'OAS1_(?P<id>[0-9]+)_MR1$')

            props['id'] = pattern.findall(subj_root)[0]
            txt_path = os.path.join(subj_root, "OAS1_{}_MR1.txt".format(props['id']))

            with open(txt_path, "r", encoding="utf8") as txtf:
                txt = txtf.read()

            props['age'] = int(re.compile(r'\nAGE:[\s]+(?P<age>[0-9]+)\n').findall(txt)[0])
            props['gender'] = re.compile(r'\nM/F:[\s]+(?P<gender>Female|Male)\n').findall(txt)[0]
            try:
                props['cdr'] = float(re.compile(r'\nCDR:[\s]+(?P<cdr>[0-9\.]+)\n').findall(txt)[0])
            except:
                props['cdr'] = 0.
            x = os.path.join(subj_root, "PROCESSED", "MPRAGE", "T88_111",
                             "OAS1_*_MR1_mpr_n*_anon_111_t88_masked_gfc.hdr")

            props['img'] = glob(x)[0]
            return props

        self.props = sorted([subjectProperties(sb) for sb in subjects], key=lambda obj: obj['id'])

    def getFilePaths(self):
        return [p['img'] for p in self.props]

    def getFileIDs(self):
        return [p['id'] for p in self.props]

    def getDataSetPrefix(self):
        return "OASIS1"

    def loadVol(self, path_file):
        return sitk.ReadImage(path_file)

    def alignToAtlas(self, vol, atlas):
        vol.SetOrigin(atlas.GetOrigin())
        vol.SetDirection(atlas.GetDirection())
        return vol
