import copy
import numpy as np
import time
import tensorflow as tf
from tensorflow import keras
import json

""" Load Models """
def load_models(file_dir):
	rewardnet = keras.models.load_model(file_dir + '/rewardnet_best.h5')
	predictnet = keras.models.load_model(file_dir + '/predictnet_best.h5')
	return rewardnet, predictnet


class Node(object):
	""" Node in the MCTS tree. """
	def __init__(self, parent, player, p):
		self.parent = parent
		self.player = player
		self.children = {} # key: next act, value: child node
		self._n = 0 # number of visits
		self._q = 0 # total rewards
		self._p = p # prior probability
		
	
	def expand(self, acts, prior):
		""" Expand the node with a list of acts and prior probabilities """
		s = 0
		r = np.random.rand()
		found_act = False
		for i in range(len(acts)):
			act = acts[i]
			p = prior[i]
			self.children[act] = Node(self, -self.player, p)
			if not found_act:
				s += p
				if s > r:
					found_act = True
					act_return = act
		if not found_act:
			act_return = act
		return act_return, self.children[act_return]
	
	
	def select(self, c1, c2):
		""" Select a child with maximum ucb """
		return max(self.children.items(), key=lambda child: child[1]._ucb(c1, c2))
	
	
	def is_leaf(self):
		""" Check if the node is a leaf node """
		return self.children == {}
	
	
	def _ucb(self, c1, c2):
		""" Upper Confidence Bounds with prior probability """
		if self._n == 0:
			return 10000
		return self._q/self._n + c2*self._p / np.sqrt(self._n) + c1*np.sqrt(2*np.log(self.parent._n)/self._n)
	
class MCTS(object):
	""" Monte Carlo Tree Search """
	def __init__(self, dim, rewardnet, predictnet, c1, c2, thres=1e-3):
		self._root = Node(None, -1, 1.0)
		self._player = 1
		self._rewardnet = rewardnet
		self._predictnet = predictnet
		self._c1 = c1
		self._c2 = c2
		self._thres = thres
		self._dim = dim
		self._acts_space = np.array([i for i in range(1, dim)])

	def set_params(self, c1, c2, thres):
		self._c1 = c1
		self._c2 = c2
		self._thres = thres
	
	def search(self, state, time_limit, ban=None):
		""" Keep searching until time_limit"""
		start_time = time.perf_counter()
		epochs = 0
		if ban:
			self._acts_space = np.array(list(set(self._acts_space.tolist()) - set(ban)))
		while True:
			state_copy = copy.deepcopy(state)
			self._search_one_epoch(state_copy)
			epochs += 1
			if time.perf_counter() - start_time > time_limit:
				break
		acts = np.array([act for act in self._root.children])
		visits = np.array([self._root.children[act]._n for act in self._root.children])
		probs = visits / visits.sum()
		idx = np.where(probs > self._thres)
		acts = acts[idx]
		probs = probs[idx] / probs[idx].sum()
		print('Epochs: %d' % epochs)
		return acts, probs


	def predict_win_rate(self, state):
		return self._reward(state)
	
	def reset(self):
		""" Reset the tree """
		self._root = Node(None, -1, 1.0)
		self._acts_space = np.array([i for i in range(1, self._dim)])
		
		
	def move(self, act):
		""" move to a child if exists """
		if act in self._root.children:
			self._root = self._root.chilren[act]
			self._root.parent = None
		else:
			self._root = Node(None, -1, 1.0)
			
	def _pick(self, state, act):
		if len(state[0]) > len(state[1]):
			state[1].append(act)
		else:
			state[0].append(act)
		
	def _search_one_epoch(self, state):
		""" Run a single playout """
		node = self._root
		# find a leaf node
		while not node.is_leaf():
			act, node = node.select(self._c1, self._c2)
			self._pick(state, act)
		# expand
		if not self._terminal(state):
			acts, prior = self._predict(state)
			act, node = node.expand(acts, prior)
			self._pick(state, act)
		state = self._playout(state)
		# update
		r = self._reward(state)
		self._update(node, r)


	def _playout(self, state):
		while not self._terminal(state):
			acts, p = self._predict(state)
			act = np.random.choice(acts, p=p)
			self._pick(state, act)
		return state

		
	def _reward(self, state):
		""" Calculate reward for a terminal state """
		if set(state[0]) == set(state[1]):
			return 0.5
		r1 = self._rewardnet([np.array([state[0]]), np.array([state[1]])])[0][0].numpy()
		r2 = self._rewardnet([np.array([state[1]]), np.array([state[0]])])[0][0].numpy()
		return (r1 + 1-r2) / 2
	
		
	def _predict(self, state):
		""" Return the possible actions with prior probs """
		length = len(state[1])
		x1 = np.pad(np.array(state[0][:length]), (0, 4-length), mode='constant')
		x2 = np.pad(np.array(state[1]), (0, 4-length), mode='constant')
		p = self._predictnet([np.array([x1]), np.array([x2])])[0].numpy()
		acts = self._acts_space
		p = p[acts] / p[acts].sum()
		idx = np.where(p > self._thres)[0]
		acts = acts[idx]
		p = p[idx] / p[idx].sum()
		acts = acts.tolist()
		return acts, p
	
		
	def _update(self, node, reward):
		""" Update total rewards and visit counts """
		while node.parent:
			if node.player == self._player:
				node._q += reward
			else:
				node._q += 1 - reward
			node._n += 1
			node = node.parent
		node._n += 1
		
		
	def _terminal(self, state):
		""" Check if the state is terminal"""
		if len(state[1]) == 5:
			return True
		return False
	
# def test():
# 	with open('./model/idx2name.json', 'r', encoding='utf-8') as f:
# 		idx2name = json.load(f)
# 	f.close()
# 	dim = 59
# 	rewardnet, predictnet = load_models('./model')

# 	player = MCTS(dim, rewardnet, predictnet, 1, 10)
# 	acts, probs = player.search([[1,26,4], [13, 58, 24]], 10, ban=[0])
# 	for i in range(len(acts)):
# 		print('%d %s: %.2f%%' % (acts[i], idx2name[str(acts[i])], probs[i]*100))

# if __name__ == '__main__':
# 	test()