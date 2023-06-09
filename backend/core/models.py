import face_recognition
import numpy as np

from PIL import Image
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, fcluster


class FaceModel:
    def __init__(self, image_item, embedding, bb):
        self.image_item = image_item
        self.embedding = embedding
        self.bb = bb

    def get_cropped_image(self):
        # todo be careful. the size might be high
        return self.image_item.get_image().crop(self.bb)

    def get_bb_percentage(self):
        return [self.bb[0] / self.image_item.im_width,
                self.bb[1] / self.image_item.im_height,
                self.bb[2] / self.image_item.im_width,
                self.bb[3] / self.image_item.im_height
        ]

    def get_extended_bb(self):
        x, y, xx, yy = self.bb
        dx = (xx - x) * 0.3
        dy = (yy - y) * 0.3
        return [
            max(0, x-dx),
            max(0, y-dy),
            min(self.image_item.im_width, xx+dx),
            min(self.image_item.im_height, yy+dy)
        ]

    def get_id(self):
        return f"{self.image_item.get_id()}|{str([f'{x:.3f}' for x in self.bb])}"


class ImageModel:
    """represents an image in the collection"""

    def __init__(self, filepath: str, do_load_faces=True):
        self.filepath = filepath
        self.faces: ["FaceModel"] = []
        if do_load_faces:
            load_faces(self)
        im = self.get_image()  # todo not load this all the time. do it in a better way
        self.im_width, self.im_height = im.size

    def get_image(self) -> Image:
        image = Image.open(self.filepath)
        # todo be careful. the size might be high
        return image

    def get_id(self):
        # todo better id?
        return self.filepath


class ClusterModel:
    def __init__(self, faces):
        self.faces = faces


##### functions
def load_faces(item: ImageModel):
    """returns face embeddings"""
    image = face_recognition.load_image_file(item.filepath)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)
    face_locations = list(map(from_fr_bb, face_locations))  # apply correction
    item.faces = [FaceModel(item, emb, bb) for emb, bb in zip(face_encodings, face_locations)]
    return item


def from_fr_bb(bb):
    (a, b, c, d) = bb
    return d, a, b, c


def to_fr_bb(bb):
    (d, a, b, c) = bb
    return a, b, c, d


def load_clusters(all_faces: [FaceModel]) -> [ClusterModel]:
    encodings = [face.embedding / np.linalg.norm(face.embedding) for face in all_faces]
    distances = pdist(encodings, metric='cosine')
    linkage_matrix = linkage(distances, method='complete')
    threshold = 0.1  # todo optimize these hyperparameters
    labels = fcluster(linkage_matrix, threshold, criterion='distance')

    cluster_map = {}
    for face, label in zip(all_faces, labels):
        mp = cluster_map.get(label, [])
        cluster_map[label] = mp
        mp.append(face)
    all_clusters = [ClusterModel(faces) for faces in cluster_map.values()]
    return all_clusters




# to_pil = transforms.ToPILImage()
#
# device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
# mtcnn = MTCNN(  # todo optimize the setting of mtcnn
#     image_size=160, margin=0, min_face_size=20,
#     thresholds=[0.6, 0.7, 0.7], factor=0.709, post_process=True, select_largest=False, keep_all=True,
#     device=device
# )


# todo. have an image preprocessing phase here
