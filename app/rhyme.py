import itertools
from Phyme import Phyme
import random
import sys
import time

random.seed(time.time())

ph = Phyme()


def get_rhyme(word):
    # Get all rhymes and merge to one list (normally separated by syllable count)
    rhymes = ph.get_perfect_rhymes(word)
    rhyme_vals = list(itertools.chain.from_iterable(list(rhymes.values())))

    # Pick a random rhyme and strip out any non alpha characters
    rhymed_word = rhyme_vals[random.randint(0, len(rhyme_vals) - 1)]
    rhymed_word = ''.join(letter for letter in rhymed_word if letter.isalpha())

    return rhymed_word.capitalize()


if __name__ == '__main__':
    print(get_rhyme(sys.argv[1]))
