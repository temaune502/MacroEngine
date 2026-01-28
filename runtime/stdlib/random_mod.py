import random

class RandomWrapper:
    def random(self): return random.random()
    def uniform(self, a, b): return random.uniform(a, b)
    def randint(self, a, b): return random.randint(a, b)
    def choice(self, seq): return random.choice(seq)
    def shuffle(self, seq): 
        random.shuffle(seq)
        return seq
