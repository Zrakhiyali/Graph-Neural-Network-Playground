# -*- coding: utf-8 -*-
"""GINCNAT.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1aJx7evOSXgK1zv7_rkTWAdtQ_f5EljFi
"""

!pip uninstall torch torchdata dgl -y
!pip install torch==1.12.0
!pip install dgl==0.9.0
!pip install torchdata==0.4.0

import os
os.environ['DGLBACKEND'] = 'pytorch'

import torch
import dgl

from torch.optim.lr_scheduler import StepLR, ReduceLROnPlateau
import numpy as np

torch.manual_seed(0)

num_nodes = 20
in_feats = 8
hid_feats = 32
out_feats = 2

s = torch.randint(low=0, high=num_nodes, size=(60,))
d = torch.randint(low=0, high=num_nodes, size=(60,))

myGraph = dgl.graph((s,d))

node_features = torch.randn(num_nodes, in_feats)
myGraph.ndata['features'] = node_features
edge_weights = torch.randn(60)
myGraph.edata['weights'] = edge_weights
myGraph.edge_index=torch.stack([s, d], dim=0)

labels = torch.randint(0, 2, (num_nodes,))
myGraph.ndata['labels'] = labels

train_mask = torch.ones(num_nodes, dtype=torch.bool)
myGraph.ndata['train_mask'] = train_mask

myGraph.ndata['train_mask'].shape

train_mask

val_mask = torch.zeros(num_nodes, dtype=torch.bool)
test_mask = torch.zeros(num_nodes, dtype=torch.bool)

val_mask

train_mask[:10] = True
val_mask[10:15] = True
test_mask[15:] = True
myGraph.ndata['val_mask'] = val_mask
myGraph.ndata['test_mask'] = test_mask

myGraph.ndata['val_mask']

myGraph

import torch.nn as nn
import torch.nn.functional as F
from dgl.nn import GraphConv

class GCN(nn.Module):
  def __init__(self,in_feat,hid_feat,out_feat):
     super(GCN, self).__init__()
     self.conv1=GraphConv(in_feat,hid_feat)
     self.conv2=GraphConv(hid_feat,out_feat)
     self.dropout=nn.Dropout(0.2)

  def forward (self,g,d_rate=0.2):
        x = self.conv1(g,g.ndata['features'])
        x = F.relu(x)
        x = F.dropout(x, p=d_rate, training=self.training)
        x = self.conv2(g, x)
        return x

model = GCN(in_feats,hid_feats,out_feats)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(),lr=.02)
schedulerGCN = StepLR(optimizer, step_size=10, gamma=0.5)

num_epochs=100

best_val_lossGCN = float('inf')
patienceGCN = 10
min_deltaGCN = 0.01
counterGCN = 0

for e in range(num_epochs):
  model.train()
  logits = model(myGraph)
  loss = loss_fn(logits[myGraph.ndata['train_mask']], myGraph.ndata['labels'][myGraph.ndata['train_mask']])
  optimizer.zero_grad()
  loss.backward()
  optimizer.step()
  with torch.no_grad():
    model.eval()
    val_logits = model(myGraph)
    val_loss = loss_fn(val_logits[myGraph.ndata['val_mask']], myGraph.ndata['labels'][myGraph.ndata['val_mask']])

  schedulerGCN.step()
  if val_loss < best_val_lossGCN - min_deltaGCN:
        best_val_lossGCN = val_loss
        counterGCN = 0
  else:
        counterGCN += 1

  if counterGCN >= patienceGCN:
        print("Early stopping triggered")
        break
  print("for epoch",e,"  train loss is ",loss.item(),"     val loss  ",val_loss.item())

with torch.no_grad():
  model.eval()
  test_logits = model(myGraph)
  test_loss = loss_fn(test_logits[myGraph.ndata['test_mask']], myGraph.ndata['labels'][myGraph.ndata['test_mask']])
  print(f"Test Loss = {test_loss.item()}")

  _, predicted = torch.max(test_logits[myGraph.ndata['test_mask']], dim=1)
  accuracy = (predicted == myGraph.ndata['labels'][myGraph.ndata['test_mask']]).float().mean()
  print(f"Test Accuracy = {accuracy.item() * 100:.2f}%")

"""**Now Try GIN**



"""

import torch
import dgl
import torch.nn as nn
import torch.nn.functional as F
from dgl.nn import GINConv
from dgl.nn.pytorch import SumPooling

class GIN(nn.Module):
    def __init__(self, in_feat, hid_feat, out_feat):
        super(GIN, self).__init__()
        self.conv1 = GINConv(
            nn.Sequential(
                nn.Linear(in_feat, hid_feat),
                nn.ReLU(),
                nn.Linear(hid_feat, hid_feat),
                nn.ReLU(),
                nn.BatchNorm1d(hid_feat),
            ),
            'sum'
        )
        self.conv2 = GINConv(
            nn.Sequential(
                nn.Linear(hid_feat, out_feat),
                nn.ReLU(),
                nn.Linear(out_feat, out_feat),
                nn.ReLU(),
                nn.BatchNorm1d(out_feat),
            ),
            'sum'
        )
        self.dropout=nn.Dropout(0.2)
    def forward (self,g,d_rate=0.2):
        x = self.conv1(g, g.ndata['features'])
        x = F.relu(x)
        x = F.dropout(x, p=d_rate, training=self.training)
        x = self.conv2(g, x)
        return x

modelGIN = GIN(in_feats,hid_feats,out_feats)
loss_fn_GIN = nn.CrossEntropyLoss()
optimizer_GIN = torch.optim.Adam(modelGIN.parameters(),lr=.02)
schedulerGIN = StepLR(optimizer, step_size=10, gamma=0.5)

num_epochs=100

best_val_lossGIN = float('inf')
patienceGIN = 10
min_deltaGIN = 0.01
counterGIN = 0

for e in range(num_epochs):
  modelGIN.train()
  logits = modelGIN(myGraph)
  loss = loss_fn_GIN(logits[myGraph.ndata['train_mask']], myGraph.ndata['labels'][myGraph.ndata['train_mask']])
  optimizer_GIN.zero_grad()
  loss.backward()
  optimizer_GIN.step()
  with torch.no_grad():
    model.eval()
    val_logits = modelGIN(myGraph)
    val_loss = loss_fn_GIN(val_logits[myGraph.ndata['val_mask']], myGraph.ndata['labels'][myGraph.ndata['val_mask']])
  schedulerGIN.step()
  if val_loss < best_val_lossGIN - min_deltaGIN:
        best_val_lossGIN = val_loss
        counterGIN = 0
  else:
        counter += 1

  if counterGIN >= patienceGIN:
        print("Early stopping triggered")
        break
  print("for epoch",e,"  train loss is ",loss.item(),"     val loss  ",val_loss.item())

with torch.no_grad():
  model.eval()
  test_logits = modelGIN(myGraph)
  test_loss = loss_fn_GIN(test_logits[myGraph.ndata['test_mask']], myGraph.ndata['labels'][myGraph.ndata['test_mask']])
  print(f"Test Loss = {test_loss.item()}")

  _, predicted = torch.max(test_logits[myGraph.ndata['test_mask']], dim=1)
  accuracy = (predicted == myGraph.ndata['labels'][myGraph.ndata['test_mask']]).float().mean()
  print(f"Test Accuracy = {accuracy.item() * 100:.2f}%")

!pip install torch-geometric

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv

class GAT(nn.Module):
    def __init__(self, in_dim, hidden_dim, out_dim, num_heads):
        super(GAT, self).__init__()
        self.conv1 = GATConv(in_dim, hidden_dim, heads=num_heads)
        self.conv2 = GATConv(hidden_dim * num_heads, out_dim, heads=1)
        self.dropout=nn.Dropout(0.2)
    def forward(self, data,d_rate=0.2):
        x, edge_index = data.ndata['features'], data.edge_index
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=d_rate, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)

num_heads = 4

from torch.optim.lr_scheduler import StepLR, ReduceLROnPlateau
import numpy as np

modelGAT = GAT(in_feats,hid_feats,out_feats,num_heads)
loss_fn_GAT = nn.CrossEntropyLoss()
optimizer_GAT = torch.optim.Adam(modelGAT.parameters(),lr=.003)
schedulerGAT = StepLR(optimizer, step_size=10, gamma=0.5)

num_epochs=100

best_val_lossGAT = float('inf')
patienceGAT = 10
min_deltaGAT = 0.01
counterGAT = 0

for e in range(num_epochs):
  modelGAT.train()
  logits = modelGAT(myGraph)
  loss = loss_fn_GAT(logits[myGraph.ndata['train_mask']], myGraph.ndata['labels'][myGraph.ndata['train_mask']])
  optimizer_GAT.zero_grad()
  loss.backward()
  optimizer_GAT.step()
  with torch.no_grad():
    model.eval()
    val_logits = modelGAT(myGraph)
    val_loss = loss_fn_GAT(val_logits[myGraph.ndata['val_mask']], myGraph.ndata['labels'][myGraph.ndata['val_mask']])
  schedulerGAT.step()
  if val_loss < best_val_lossGAT - min_deltaGAT:
        best_val_lossGAT = val_loss
        counterGAT = 0
  else:
        counterGAT += 1

  if counterGAT >= patienceGAT:
        print("Early stopping triggered")
        break
  print("for epoch",e,"  train loss is ",loss.item(),"     val loss  ",val_loss.item())

with torch.no_grad():
  model.eval()
  test_logits = modelGAT(myGraph)
  test_loss = loss_fn_GAT(test_logits[myGraph.ndata['test_mask']], myGraph.ndata['labels'][myGraph.ndata['test_mask']])
  print(f"Test Loss = {test_loss.item()}")

  _, predicted = torch.max(test_logits[myGraph.ndata['test_mask']], dim=1)
  accuracy = (predicted == myGraph.ndata['labels'][myGraph.ndata['test_mask']]).float().mean()
  print(f"Test Accuracy = {accuracy.item() * 100:.2f}%")