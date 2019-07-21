# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

import numpy as np
import logging

from block_zoo.BaseLayer import BaseConf
from utils.DocInherit import DocInherit
from utils.exceptions import ConfigurationError
import copy

class Combination2DConf(BaseConf):
    """ Configuration for combination layer
    Args:
        operations (list):  a subset of ["cosine", "bilinear"].
    """
    def __init__(self, **kwargs):
        super(Combination2DConf, self).__init__(**kwargs)

    @DocInherit
    def default(self):
        self.operations = ["cosine", "bilinear"]

    @DocInherit
    def declare(self):
        self.num_of_inputs = -1
        self.input_ranks = [-1]

    @DocInherit
    def inference(self):
        self.output_dim = [self.input_dims[0][0], len(self.operations), self.input_dims[0][1], self.input_dims[1][1]]

        super(Combination2DConf, self).inference()

    @DocInherit
    def verify(self):
        super(Combination2DConf, self).verify()

        # to check if the ranks of all the inputs are equal
        rank_equal_flag = True
        for i in range(len(self.input_ranks)):
            if self.input_ranks[i] != self.input_ranks[0]:
                rank_equal_flag = False
                break
        if rank_equal_flag == False:
            raise ConfigurationError("For layer Combination, the ranks of each inputs should be consistent!")

            
class Combination2D(nn.Module):
    """ Combination2D layer to merge the representation of two sequence
    Args:
        layer_conf (Combination2DConf): configuration of a layer
    """
    def __init__(self, layer_conf):
        super(Combination2D, self).__init__()
        self.layer_conf = layer_conf

        self.weight_bilinear = torch.nn.Linear(self.layer_conf.input_dims[0][-1], self.layer_conf.input_dims[0][-1])


        logging.warning("The length Combination layer returns is the length of first input")

    def forward(self, *args):
        """ process inputs
        Args:
            args (list): [string, string_len, string2, string2_len, ...]
                e.g. string (Variable): [batch_size, dim], string_len (ndarray): [batch_size]
        Returns:
            Variable: [batch_size, output_dim], None
        """

        result = []
        if "cosine" in self.layer_conf.operations:
            string1 = args[0]
            string2 = args[2]
            result_multiply = torch.matmul(string1, string2.transpose(1,2))

            # normalize
            #norm_matrix = torch.matmul(torch.norm(string1, p=2, dim=-1).unsqueeze(-1), torch.norm(string2, p=2, dim=-1).unsqueeze(-1).transpose(1,2))
            #result_multiply = result_multiply / norm_matrix

            result.append(torch.unsqueeze(result_multiply, 1))

        if "bilinear" in self.layer_conf.operations:
            string1 = args[0]
            string2 = args[2]
            string1 = self.weight_bilinear(string1)
            result_multiply = torch.matmul(string1, string2.transpose(1,2))

            result.append(torch.unsqueeze(result_multiply, 1))

        return torch.cat(result, 1), args[1]
