from Phyme import Phyme
import random
import sys
import time

random.seed(time.clock())

ph = Phyme()

rhymes = ph.get_perfect_rhymes(sys.argv[1])
rhyme_vals = []

for arr in rhymes.values():
    for rhyme in arr:
        rhyme_vals.append(rhyme)

print(rhyme_vals[random.randint(0, len(rhyme_vals))].capitalize())
