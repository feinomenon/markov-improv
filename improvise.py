import mingus.core.notes as notes
from mingus.containers.Note import Note
from mingus.midi import fluidsynth

from collections import defaultdict
from collections import Counter
import random
import bisect
import os.path
import json

C4 = 48
LOW = .000000000000001

def get_counts(file, n):
    """Create a counts dictionary given a file containing n-grams (for now)."""
    ngrams = defaultdict(Counter)
    with open(file, 'r') as f:
        for line in f.readlines():
            parts = line.split()    # Split on all whitespace
            if parts:
                prev = ' '.join(parts[:n])
                curr = int(parts[n])
                count = int(parts[-1])
                ngrams[prev][curr] += count
    return ngrams

def get_probs(counts):
    """Create a probability dictionary given a counts dictionary."""
    probs_dict = defaultdict(lambda: defaultdict(lambda: LOW))
    for prev in counts:
        total_counts = float(sum(counts[prev].values()))
        for curr in counts[prev]:
            prob = counts[prev][curr] / total_counts
            probs_dict[prev][curr] = prob
    return probs_dict

def accumulate(lst):
    """Python 2: Helper function to get cumulative sums of items in a list."""
    total = 0
    for x in lst:
        total += x
        yield total

def sample_note(dist_dict):
    """Given a distribution dictionary, generate the next note."""
    # TODO: Add constraints for lowest & highest notes
    notes, probs = zip(*dist_dict.items())
    acc_probs = list(accumulate(probs))
    rand = random.random() * acc_probs[-1]
    choice = notes[bisect.bisect(acc_probs, rand)]
    return choice

def stream_notes(probs_dict):
    """Generate a sequence of notes based on the probs dictionary."""
    prev = random.choice(probs_dict.keys())
    out = []
    while True:
        curr = sample_note(probs_dict[prev])
        prev = prev.split(' ')
        prev = ' '.join((prev[1], prev[2], prev[3], curr))
        if prev in probs_dict:
            yield curr

def main():
    if not os.path.isfile('./data/probs.json'):
        print ('Creating json file...')
        fname = "./data/interval-5gram.csv"
        counts = get_counts(fname, 4)
        probs = get_probs(counts)
        with open('./data/probs.json', 'w') as outfile:
            json.dump(probs, outfile)

    with open('./data/probs.json', 'r') as infile:
        probs_dict = json.load(infile, encoding='utf-8')

    start_int = C4
    melody = []
    fluidsynth.init("/usr/share/sounds/sf2/FluidR3_GM.sf2", "alsa")

    streamer = stream_notes(probs_dict)
    for i in range(100):
        next_int = start_int + int(next(streamer))
        next_note = Note()
        next_note.from_int(next_int)

        melody.append(next_note)
        start_int = next_int
        print(next_note)
        fluidsynth.play_Note(next_note)
        time.sleep(.2)

if __name__ == '__main__':
    main()
