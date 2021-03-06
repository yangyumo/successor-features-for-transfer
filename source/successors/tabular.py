from collections import defaultdict
from copy import deepcopy
import numpy as np

from successors.successor import SF


class TabularSF(SF):
    """
    A successor feature representation implemented using lookup tables. Storage is lazy and implemented efficiently
    using defaultdict.
    """
    
    def __init__(self, alpha, *args, noise_init=lambda size: np.random.uniform(-0.01, 0.01, size=size), **kwargs):
        """
        Creates a new tabular representation of successor features.
        
        Parameters
        ----------
        alpha : float
            the learning rate
        noise_init : function 
            instruction to initialize action-values, defaults to Uniform[-0.01, 0.01]
        """
        super(TabularSF, self).__init__(*args, **kwargs)
        self.alpha = alpha
        self.noise_init = noise_init
    
    def build_successor(self, task, source=None):
        if source is None or self.n_tasks == 0:
            n_actions = task.action_count()
            n_features = task.feature_dim()
            return defaultdict(lambda: self.noise_init((n_actions, n_features)))
        else:
            return deepcopy(self.psi[source])
                
    def get_successor(self, state, policy_index):
        return np.expand_dims(self.psi[policy_index][state], axis=0)
        
    def get_successors(self, state):
        return np.expand_dims(np.array([psi[state] for psi in self.psi]), axis=0)

    def update_successor(self, state, action, phi, next_state, next_action, gamma, policy_index):
        psi = self.psi[policy_index]
        targets = phi.flatten() + gamma * psi[next_state][next_action,:] 
        psi[state][action,:] = psi[state][action,:] + self.alpha * (targets - psi[state][action,:])
    
    def update_successor_on_batch(self, states, actions, phis, next_states, gammas, policy_index):
        
        # next actions come from GPI
        next_actions = []
        for state in states:
            q, _ = self.GPI(state, policy_index)
            next_action = np.argmax(np.max(q, axis=1))
            next_actions.append(next_action)
        
        # update sequentially on each example
        for tup in zip(states, actions, phis, next_states, next_actions, gammas):
            self.update_successor(*tup, policy_index)
            
