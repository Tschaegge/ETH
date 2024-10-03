import torch

from math import e
from pdb import set_trace

def scale_prediced_values(states, predicted_values, method, max_scale=10):

    if method == "identity": 
        return predicted_values

    scaled_predicted_values = predicted_values.clone().detach()
    n = states.shape[0]
    for i in range(n):
        if method == "negative":
            # choice 1: x * -1
            scaled_predicted_values[i] = scaled_predicted_values[i] * -1.
        elif method == "exponential decay":
            # choice 2: e ** -x
            scaled_predicted_values[i] = e ** - scaled_predicted_values[i]
        elif method == "sigmoid complement":
            # choice 3: 1 - 1/(1 + e^(-x))
            scaled_predicted_values[i] = 1 - 1/(1 + e ** - scaled_predicted_values[i])
        elif method == "negative tanh":
            scaled_predicted_values[i] = -1. * torch.tanh(scaled_predicted_values[i])
        elif method == "negative cubic":
            scaled_predicted_values[i] = -1. * (scaled_predicted_values[i] ** 3)
        elif method == "hash":
            h = hash("".join([str(x.item()) for x in states[i,:,:,-1].flatten()]))
            # hash: doesn't work?
            scaled_predicted_values[i] = scaled_predicted_values[i] * (h % max_scale + 1) # / max_scale
    return scaled_predicted_values.detach()