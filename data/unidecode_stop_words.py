from unidecode import unidecode

with open('stop.words', 'r') as f:
        sw = f.read().split(',')
        sw = [word.strip() for word in sw]
        sw = sw[:-1]

sw_asiifold = [unidecode(w) for w in sw]
all_sw = sw + sw_asiifold

with open('stop.words.asciifold', 'w') as f:
    f.write(', '.join(all_sw))
