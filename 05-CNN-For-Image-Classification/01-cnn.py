
# coding: utf-8

# # 4. 딥러닝으로 패션 아이템 구분하기
# Fashion MNIST 데이터셋과 앞서 배운 인공신경망을 이용하여 패션아이템을 구분해봅니다.
# 본 튜토리얼은 PyTorch의 공식 튜토리얼 (https://github.com/pytorch/examples/blob/master/mnist/main.py)을 참고하여 만들어졌습니다.

import torch
import torchvision
import torch.nn.functional    as F
from torch import nn, optim
from torch.autograd import Variable
from torchvision import transforms, datasets


use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")


batch_size = 64


transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])


# ## 데이터셋 불러오기

trainset = datasets.FashionMNIST(
    root      = './.data/', 
    train     = True,
    download  = True,
    transform = transform
)
testset = datasets.FashionMNIST(
    root      = './.data/', 
    train     = False,
    download  = True,
    transform = transform
)

train_loader = torch.utils.data.DataLoader(
    dataset     = trainset,
    batch_size  = batch_size,
    shuffle     = True,
)
test_loader = torch.utils.data.DataLoader(
    dataset     = testset,
    batch_size  = batch_size,
    shuffle     = True,
)


# ## 뉴럴넷으로 Fashion MNIST 학습하기

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear(320, 50)
        self.fc2 = nn.Linear(50, 10)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


# ## 하이퍼파라미터 
# `to()` 함수는 모델의 파라미터들을 지정한 곳으로 보내는 역할을 합니다. 일반적으로 CPU 1개만 사용할 경우 필요는 없지만, GPU를 사용하고자 하는 경우 `to("cuda")`로 지정하여 GPU로 보내야 합니다. 지정하지 않을 경우 계속 CPU에 남아 있게 되며 빠른 훈련의 이점을 누리실 수 없습니다.
# 최적화 알고리즘으로 파이토치에 내장되어 있는 `optim.SGD`를 사용하겠습니다.

model        = Net().to(device)
optimizer    = optim.SGD(model.parameters(), lr=0.01, momentum=0.5)
epochs       = 10
log_interval = 100


# ## 훈련하기

def train(model, device, train_loader, optimizer, epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.cross_entropy(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.item()))


# ## 테스트하기
# 아무리 훈련이 잘 되었다고 해도 실제 데이터를 만났을때 성능이 낮다면 쓸모 없는 모델일 것입니다. 우리가 진정 원하는 것은 훈련 데이터에 최적화한 모델이 아니라 모든 데이터에서 높은 성능을 보이는 모델이기 때문입니다. 세상에 존재하는 모든 데이터에 최적화 하는 것을 "일반화"라고 부르고 모델이 얼마나 실제 데이터에 적응하는지를 수치로 나타낸 것을 "일반화 오류"(Generalization Error) 라고 합니다. 
# 우리가 만든 모델이 얼마나 일반화를 잘 하는지 알아보기 위해, 그리고 언제 훈련을 멈추어야 할지 알기 위해 매 이포크가 끝날때 마다 테스트셋으로 모델의 성능을 측정해보겠습니다.

def test(model, device, test_loader):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.cross_entropy(output, target, size_average=False).item() # sum up batch loss
            pred = output.max(1, keepdim=True)[1] # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))


# ## 코드 돌려보기
# 자, 이제 모든 준비가 끝났습니다. 코드를 돌려서 실제로 훈련이 되는지 확인해봅시다!

for epoch in range(1, epochs + 1):
    train(model, device, train_loader, optimizer, epoch)
    test(model, device, test_loader)

