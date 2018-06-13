# CEPEND: Contingent Event Pair Extractor for Natural Disasters

CEPEND is developed to extract contingent event pairs in the domain of natural disasters. The following data sources are used:

- Wikipedia
- Wikinews
- Reuters RCV1

This application may behave unexpectedly if the environment is not exactly as it should be. If problems are encountered, please contact <w.de.vries.21@student.rug.nl>.

## Requirements

- Linux or MacOS (Windows may work, but not tested)
- Python3.6 (may work on 3.5, but not tested)
- Pipenv

## Installation

Download the source code and run `pipenv install && pipenv shell`. The `data` directory has to be populated with the following data:

- `TemProb.txt` > Only used if the `--reorder` option is used. [https://github.com/qiangning/TemProb-NAACL18/blob/master/data/TemProb.txt]
- `Sauri-lexicon-tabformat.txt` > Used for filtering events. Can be an empty file. E-mail me for help. Factuality lexicon developed by (Sauri, 2008: A factuality profiler for eventualities in text.)
- `reuters/*` The Reuters RCV1 news corpus. If not available, disable the usage of this corpus by using the `-d wiki wikinews` option. Directory should have the following structure:
    - `disk1/`
        - `19960820/`
            - `2286newsML.xml`
            - [...]
        - [...]
    - `disk2/`
        - [...]

## Usage

```
usage: start.py [-h]
                [-d {wiki,wikinews,reuters} [{wiki,wikinews,reuters} ...]]
                [-a {index,download,totext,dedup,events,event_pairs,rank_pairs,-,test} [{index,download,totext,dedup,events,event_pairs,rank_pairs,-,test} ...]]
                [-k K] [-c C] [-p {all,root,clause-root,best}]
                [-m {adjacent,within,outside}] [--reorder ] [--per-source ]
                [-e {pmi,cp,scp}] [-n N] [-q {1,2,3,4} [{1,2,3,4} ...]]
                [-r {all,even,odd,none}] [-s S]

CEPEND: Contingent Event Pair Extractor for Natural Disasters

optional arguments:
  -h, --help            show this help message and exit
  -d {wiki,wikinews,reuters} [{wiki,wikinews,reuters} ...]
                        List of data collection to use. (default: ['wiki',
                        'wikinews', 'reuters'])
  -a {index,download,totext,dedup,events,event_pairs,rank_pairs,-,test} [{index,download,totext,dedup,events,event_pairs,rank_pairs,-,test} ...]
                        Actions to perform. When 2 items are given, all
                        intermediate actions are also performed. (default:
                        ['index', 'rank_pairs'])
  -k K                  Max # documents per category per data collection
                        [events step].
  -c C                  Min event pair frequency [event_pairs step] (default:
                        10)
  -p {all,root,clause-root,best}
                        Pair dependencies [event_pairs step] (default: all)
  -m {adjacent,within,outside}
                        Pair method [event_pairs step] (default: outside)
  --reorder []          Set all pairs in most probable order with TemProb
                        [event_pairs step]
  --per-source []       Enable event pair extraction per source [event_pairs
                        step]
  -e {pmi,cp,scp}       Event pair ranking metric [rank_pairs step]
  -n N                  How many event pairs to save (per quarter) [rank_pairs
                        step]
  -q {1,2,3,4} [{1,2,3,4} ...]
                        Which quarters of ranked list to save [rank_pairs
                        step]
  -r {all,even,odd,none}
                        Remove argument information for event pairs.
                        [rank_pairs step] (default: none)
  -s S                  Random seed
```