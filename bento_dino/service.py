import numpy as np
from PIL import Image
from torch import hub, no_grad
from torchvision import transforms

import bentoml
from bentoml.io import Image as BentoImage, JSON

dinov2 = hub.load('facebookresearch/dinov2', 'dinov2_vitb14_reg')

transform = transforms.Compose([
    transforms.Resize(518),
    transforms.CenterCrop(518),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

@bentoml.service(name="dinov2_service", traffic={"timeout": 300})
class DinoService:
    @bentoml.api
    def extract(self, image: Image.Image) -> dict:
        tensor = transform(image).unsqueeze(0)

        with no_grad():
            output = dinov2(tensor)

        vec = output.squeeze().cpu().numpy().astype(np.float32)
        return {"vector": vec.tolist()}
