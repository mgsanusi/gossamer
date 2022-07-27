import shelve
import pathlib
import os

current_dir = pathlib.Path(__file__).parent.resolve()
prediction_files = [f for f in os.listdir(current_dir) if f.endswith(".predictions")]
assert len(prediction_files) == 1, "Exactly 1 prediction file must be present in the ../gossamer/app/credtweak_models directory"

prediction = os.path.join(current_dir, prediction_files[0])

s = shelve.open("pass2path.shelve")

with open(prediction, "r") as f:
    lines = f.read().strip().split("\n")
    for line in lines:
        split_line = line.strip().split("\t")
        if len(split_line) < 2: continue
        l = eval(split_line[1])
        s[split_line[0]] = l
