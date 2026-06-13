import torch
import torch.nn as nn
import torchvision.models as models

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# model = models.convnext_tiny(pretrained=False)
# model.classifier[2] = nn.Linear(model.classifier[2].in_features, 7)

# model.load_state_dict(torch.load("emotion_model.pth", map_location=device))
model = models.resnet18(weights="DEFAULT")
model.fc = nn.Sequential(
    nn.Dropout(0.4),
    nn.Linear(512, 7)
)
model.load_state_dict(torch.load("best_model.pth", map_location=device, weights_only=False))
model = model.to(device)

model.eval()