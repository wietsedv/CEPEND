from glob import glob
import os
import random
import sys
from shutil import copyfile
import util


os.chdir(sys.argv[1])

files = [filepath for filepath in glob('plaintext/*/*.txt') if not filepath.startswith('plaintext/unrelated')]
files = random.sample(files, 50)
util.ensure_empty_dir('plaintext-sample')
for filepath in files:
    filename = filepath.split('/')[-1]
    copyfile(filepath, os.path.join('plaintext-sample', filename))
