from PIL import Image
import numpy as np
from torch import hub, no_grad
from torchvision import transforms


dinov2_vitb14_reg = hub.load('facebookresearch/dinov2', 'dinov2_vitb14_reg')


transform = transforms.Compose([
    transforms.Resize(518),                   # original: 518
    transforms.CenterCrop(518),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],           # ImageNet-Normalisierung
        std=[0.229, 0.224, 0.225]
    )
])


def gen_vector(path_to_image: str):
    """
    Generiert einen Einbettungsvektor für ein einzelnes Bild.
    """
    image = Image.open(path_to_image).convert("RGB")
    input_tensor = transform(image).unsqueeze(0)  # (1, 3, H, W)

    with no_grad():
        output = dinov2_vitb14_reg(input_tensor)

    embedding_vector = output.squeeze().cpu().numpy().astype(np.float32)
    return embedding_vector
