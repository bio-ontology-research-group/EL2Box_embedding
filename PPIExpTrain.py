#!/usr/bin/env python
import click as ck
import numpy
import torch.optim as optim
from model.ELBoxlModel import  ELBoxModel
from utils.elDataLoader import load_data, load_valid_data
import logging
import torch
logging.basicConfig(level=logging.INFO)
from utils.plot_embeddings import plot_embeddings
import pandas as pd
import  numpy as np
@ck.command()
#family_normalized.owl
#yeast-classes-normalized.owl
@ck.option(
    '--data-file', '-df', default='data/data-train/yeast-classes-normalized.owl',
    help='Normalized ontology file (Normalizer.groovy)')
@ck.option(
    '--valid-data-file', '-vdf', default='data/valid/4932.protein.links.v10.5.txt',
    help='Validation data set')
@ck.option(
    '--out-classes-file', '-ocf', default='data/classPPIEmbed.pkl',
    help='Pandas pkl file with class embeddings')
@ck.option(
    '--out-relations-file', '-orf', default='data/relationPPIEmbed.pkl',
    help='Pandas pkl file with relation embeddings')
@ck.option(
    '--batch-size', '-bs', default=512,
    help='Batch size')
@ck.option(
    '--epochs', '-e', default=1000,
    help='Training epochs')
@ck.option(
    '--device', '-d', default='gpu:0',
    help='GPU Device ID')
@ck.option(
    '--embedding-size', '-es', default=50,
    help='Embeddings size')
@ck.option(
    '--reg-norm', '-rn', default=1,
    help='Regularization norm')
@ck.option(
    '--margin', '-m', default=-0.1,
    help='Loss margin')
@ck.option(
    '--learning-rate', '-lr', default=0.01,
    help='Learning rate')
@ck.option(
    '--params-array-index', '-pai', default=-1,
    help='Params array index')
@ck.option(
    '--loss-history-file', '-lhf', default='data/loss_history.csv',
    help='Pandas pkl file with loss history')


def main(data_file, valid_data_file, out_classes_file, out_relations_file,
         batch_size, epochs, device, embedding_size, reg_norm, margin,
         learning_rate, params_array_index, loss_history_file):

    device = torch.device('cuda:0')

    #training procedure
    train_data, classes, relations = load_data(data_file)
    print(len(relations))
    embedding_dim = 50
    model = ELBoxModel(device,classes, len(relations), embedding_dim=embedding_dim, batch = batch_size,margin1=-0.05)

    #
    # checkpoint = torch.load('./netPlot.pkl')
    # model.load_state_dict(checkpoint.state_dict())  # 加载网络权重参数

    optimizer = optim.Adam(model.parameters(), lr=0.001)
    model = model.to(device)
    train(model,train_data, optimizer,classes, relations)
    model.eval()

    model = model.to('cuda:0')

    cls_file = out_classes_file
    df = pd.DataFrame(
        {'classes': list(classes.keys()),
         'embeddings': list(model.classEmbeddingDict.weight.clone().detach().cpu().numpy())})
    df.to_pickle(cls_file)



    rel_file = out_relations_file
    df = pd.DataFrame(
        {'relations': list(relations.keys()),
         'embeddings': list(model.relationEmbeddingDict.weight.clone().detach().cpu().numpy())})

    df.to_pickle(rel_file)

def train(model, data, optimizer, aclasses, relations, num_epochs=7000):
    model.train()

    for epoch in range(num_epochs):
        re = model(data)
        loss = sum(re)
        if epoch % 1000 == 0:
            print('epoch:',epoch,'loss:',round(loss.item(),3))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

if __name__ == '__main__':
    main()