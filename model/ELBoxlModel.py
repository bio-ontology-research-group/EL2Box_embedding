import numpy as np
import torch.nn as nn
import torch
np.random.seed(12)


class RelationModel(nn.Module):
    def __init__(self, embedding_dim):
        self.embedding_dim = embedding_dim
        super(RelationModel, self).__init__()


        self.mlp = nn.Sequential(
            nn.Linear( 2*embedding_dim, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.Tanh(),
            nn.Linear(embedding_dim, embedding_dim),


           # nn.LayerNorm(16*embedding_dim),
           #  nn.Tanh(),
           #  nn.Linear(16 * embedding_dim,  8*embedding_dim),
           # nn.LayerNorm(embedding_dim * 8),
           #  nn.Tanh(),
           #  nn.Linear(8 * embedding_dim, 2 * embedding_dim),
           # nn.LayerNorm(embedding_dim * 2),
           #  nn.Tanh(),
           #  nn.Linear(2*embedding_dim,  embedding_dim),
           # nn.LayerNorm(embedding_dim),
           #  nn.Tanh(),
        )

    def forward(self, input):
        #input[:,:50]
        return  input[:,:50]
class ELBoxModel(nn.Module):
    '''

    Args:
        classNum: number of classes
        relationNum: number of relations
        embedding_dim: the dimension of the embedding(both class and relatio)
        margin: the distance that two box apart
    '''

    def __init__(self, device, class_, relationNum, embedding_dim, batch,margin1=0):
        super(ELBoxModel, self).__init__()

        self.margin1 = margin1
        self.margin=0
        self.classNum = len(class_)
        self.class_ = class_
        self.relationNum = relationNum
        self.device = device
        self.reg_norm=1
        self.inf=4

        self.classEmbeddingDict = nn.Embedding(self.classNum, embedding_dim*2)
        nn.init.uniform_(self.classEmbeddingDict.weight, a=-1, b=1)
        self.classEmbeddingDict.weight.data /= torch.linalg.norm(self.classEmbeddingDict.weight.data,axis=1).reshape(-1,1)

        self.relationEmbeddingDict = nn.Embedding(relationNum, embedding_dim)
        nn.init.uniform_(self.relationEmbeddingDict.weight,a=-1,b=1)
        self.relationEmbeddingDict.weight.data /= torch.linalg.norm(
            self.relationEmbeddingDict.weight.data, axis=1).reshape(-1, 1)

        self.embedding_dim = embedding_dim
        self.relationModel = RelationModel(self.embedding_dim)
        self.tailRelationModel = self.relationModel
        for m in self.relationModel.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                nn.init.kaiming_normal_(m.weight)

        for m in self.tailRelationModel.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                nn.init.kaiming_normal_(m.weight)



    # cClass isSubSetof dClass

    def nf1Loss(self, input):
        c = self.classEmbeddingDict(input[:, 0])
        d = self.classEmbeddingDict(input[:, 1])

        c1 = c[:, :self.embedding_dim]
        d1 = d[:, :self.embedding_dim]

        c2 = torch.abs(c[:, self.embedding_dim:])
        d2 = torch.abs(d[:, self.embedding_dim:])

        # box

        cr = torch.abs(c2)
        dr = torch.abs(d2)

        margin = (torch.ones(d1.shape, requires_grad=False) * self.margin1).to(self.device)
        zeros = (torch.zeros(d1.shape, requires_grad=False)).to(self.device)

        cen1 = c1
        cen2 = d1
        euc = torch.abs(cen1 - cen2)

        dst = torch.reshape(torch.linalg.norm(torch.maximum(euc + cr - dr+margin , zeros), axis=1), [-1, 1])
      #  print(cr)

        return dst
    # cClass and dCLass isSubSetof eClass
    def nf2Loss(self, input):
        c = self.classEmbeddingDict(input[:, 0])
        d = self.classEmbeddingDict(input[:, 1])
        e = self.classEmbeddingDict(input[:, 2])
        c1 = c[:, :self.embedding_dim]
        d1 = d[:, :self.embedding_dim]
        e1 = e[:, :self.embedding_dim]

        c2 = torch.abs(c[:, self.embedding_dim:])
        d2 =torch.abs( d[:, self.embedding_dim:])
        e2 = torch.abs(e[:, self.embedding_dim:])



        startAll = torch.maximum(c1-c2, d1-d2)
        endAll = torch.minimum(c1 + c2, d1 + d2)

        newR = torch.abs(startAll-endAll)/2
        er = torch.abs(e2)

        margin = (torch.ones(d1.shape, requires_grad=False) * self.margin1).to(self.device)
        zeros = (torch.zeros(d1.shape, requires_grad=False)).to(self.device)

        cen1 =(startAll+endAll)/2
        cen2 = e1
        euc = torch.abs(cen1 - cen2)

        dst = torch.reshape(torch.linalg.norm(torch.maximum(euc + newR - er +margin , zeros), axis=1), [-1, 1])\
        +torch.linalg.norm(torch.maximum(startAll-endAll , zeros), axis=1)
        return dst
    def disJointLoss(self, input):
        c = self.classEmbeddingDict(input[:, 0])
        d = self.classEmbeddingDict(input[:, 1])

        c1 = c[:, :self.embedding_dim]
        d1 = d[:, :self.embedding_dim]

        c2 = torch.abs(c[:, self.embedding_dim:])
        d2 = torch.abs(d[:, self.embedding_dim:])

        # box

        cr = torch.abs(c2)
        dr = torch.abs(d2)

        margin = (torch.ones(d1.shape, requires_grad=False) * self.margin1).to(self.device)
        zeros = (torch.zeros(d1.shape, requires_grad=False)).to(self.device)

        cen1 = c1
        cen2 = d1
        euc = torch.abs(cen1 - cen2)

        dst = torch.reshape(torch.linalg.norm(torch.maximum(-euc + cr + dr+margin , zeros), axis=1), [-1, 1])

        return dst



    def nf3Loss(self, input):
        c = self.classEmbeddingDict(input[:, 0])
        r = self.relationEmbeddingDict(input[:, 1])
        d = self.classEmbeddingDict(input[:, 2])

        c1_o = c[:, :self.embedding_dim]
        c2_o = c[:, self.embedding_dim:]

        d1_o = d[:, :self.embedding_dim]
        d2_o = d[:, self.embedding_dim:]

        c1_input = torch.cat((c1_o, r), dim=1)
        c2_input = torch.cat((c2_o, r), dim=1)

        d1_input = torch.cat((d1_o, r), dim=1)
        d2_input = torch.cat((d2_o, r), dim=1)

        c1 = self.relationModel(c1_input)
        c2 = torch.abs(self.relationModel(c2_input))

        d1 = self.tailRelationModel(d1_input)
        d2 = torch.abs(self.tailRelationModel(d2_input))

        cr = torch.abs(c2)
        dr = torch.abs(d2)

        margin = (torch.ones(d1.shape, requires_grad=False) * self.margin1).to(self.device)
        zeros = (torch.zeros(d1.shape, requires_grad=False) ).to(self.device)

        cen1 = c1+r
        cen2 = d1
        euc = torch.abs(cen1-cen2)

        dst = torch.reshape(torch.linalg.norm(torch.maximum( euc+cr-dr +margin , zeros), axis=1),[-1,1])

        return  dst

    def neg_loss(self, input):
        c = self.classEmbeddingDict(input[:, 0])
        r = self.relationEmbeddingDict(input[:, 1])
        d = self.classEmbeddingDict(input[:, 2])

        c1_o = c[:, :self.embedding_dim]
        c2_o = c[:, self.embedding_dim:]

        d1_o = d[:, :self.embedding_dim]
        d2_o = d[:, self.embedding_dim:]

        c1_input = torch.cat((c1_o, r), dim=1)
        c2_input = torch.cat((c2_o, r), dim=1)

        d1_input = torch.cat((d1_o, r), dim=1)
        d2_input = torch.cat((d2_o, r), dim=1)

        c1 = self.relationModel(c1_input)
        c2 = torch.abs(self.relationModel(c2_input))

        d1 = self.tailRelationModel(d1_input)
        d2 = torch.abs(self.tailRelationModel(d2_input))

        cr = torch.abs(c2)
        dr = torch.abs(d2)

        margin = (torch.ones(d1.shape, requires_grad=False) * self.margin1).to(self.device)
        zeros = (torch.zeros(d1.shape, requires_grad=False)).to(self.device)

        cen1 = c1 + r
        cen2 = d1
        euc = torch.abs(cen1 - cen2)

        dst = torch.reshape(torch.linalg.norm(torch.maximum(euc - cr - dr-margin , zeros), axis=1), [-1, 1])

        return dst


    # relation some cClass isSubSet of dClass
    def nf4Loss(self, input):
        c = self.classEmbeddingDict(input[:, 1])

        r = self.relationEmbeddingDict(input[:, 0])

        d = self.classEmbeddingDict(input[:, 2])

        c1_o = c[:, :self.embedding_dim]
        c2_o = c[:, self.embedding_dim:]

        d1_o = d[:, :self.embedding_dim]
        d2_o = d[:, self.embedding_dim:]

        c1_input = torch.cat((c1_o, r), dim=1)
        c2_input = torch.cat((c2_o, r), dim=1)

        d1_input = torch.cat((d1_o, r), dim=1)
        d2_input = torch.cat((d2_o, r), dim=1)

        c1 = self.relationModel(c1_input)
        c2 = torch.abs(self.relationModel(c2_input))

        d1 = self.tailRelationModel(d1_input)
        d2 = torch.abs( self.tailRelationModel(d2_input))

        cr = torch.abs(c2)
        dr = torch.abs(d2)

        margin = (torch.ones(d1.shape, requires_grad=False) * self.margin1).to(self.device)
        zeros = (torch.zeros(d1.shape, requires_grad=False)).to(self.device)

        cen1 = c1 - r
        cen2 = d1
        euc = torch.abs(cen1 - cen2)

        dst = torch.reshape(torch.linalg.norm(torch.maximum(euc - cr - dr+margin  , zeros), axis=1), [-1, 1])

        return dst






    def forward(self, input):
        batch = 512

        rand_index = np.random.choice(len(input['nf1']), size=batch)
        nf1Data = input['nf1'][rand_index]
        nf1Data = nf1Data.to(self.device)
        loss1 = self.nf1Loss(nf1Data)
        mseloss = nn.MSELoss(reduce=True)
        loss1 = mseloss(loss1, torch.zeros(loss1.shape, requires_grad=False).to(self.device))

        # nf2
        rand_index = np.random.choice(len(input['nf2']), size=batch)
        nf2Data = input['nf2'][rand_index]
        nf2Data = nf2Data.to(self.device)
        loss2 = self.nf2Loss(nf2Data)
        mseloss = nn.MSELoss(reduce=True)
        loss2 = mseloss(loss2, torch.zeros(loss2.shape, requires_grad=False).to(self.device))

        # nf3
        rand_index = np.random.choice(len(input['nf3']), size=batch)
        nf3Data = input['nf3'][rand_index]
        nf3Data = nf3Data.to(self.device)
        loss3 = self.nf3Loss(nf3Data)
        mseloss = nn.MSELoss(reduce=True)
        loss3 = mseloss(loss3, torch.zeros(loss3.shape, requires_grad=False).to(self.device))

        # nf4
        rand_index = np.random.choice(len(input['nf4']), size=batch)
        nf4Data = input['nf4'][rand_index]
        nf4Data = nf4Data.to(self.device)
        loss4 = self.nf4Loss(nf4Data)
        mseloss = nn.MSELoss(reduce=True)
        loss4 = mseloss(loss4, torch.zeros(loss4.shape, requires_grad=False).to(self.device))

        # disJoint
        rand_index = np.random.choice(len(input['disjoint']), size=batch)
        disJointData = input['disjoint'][rand_index]
        disJointData = disJointData.to(self.device)
        disJointLoss = self.disJointLoss(disJointData)
        mseloss = nn.MSELoss(reduce=True)
        disJointLoss = mseloss(disJointLoss, torch.zeros(disJointLoss.shape, requires_grad=False).to(self.device))
        # negLoss
        rand_index = np.random.choice(len(input['nf3_neg']), size=batch)
        negData = input['nf3_neg'][rand_index]
        negData = negData.to(self.device)
        negLoss = self.neg_loss(negData)

        mseloss = nn.MSELoss(reduce=True)
        negLoss = mseloss(negLoss, torch.ones(negLoss.shape, requires_grad=False).to(self.device)*2)


        totalLoss = [loss1+loss2+disJointLoss+loss3+loss4+negLoss]  # +negLoss #loss4 +disJointLoss+loss1 + loss2 +  negLoss#+ disJointLoss+ topLoss+ loss3 + loss4 +  negLoss

        return (totalLoss)
