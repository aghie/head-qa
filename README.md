# HEAD-QA

This repository contains the sources used in "HEAD-QA: A Healthcare Dataset for Complex Reasoning" (ACL, 2019)

HEAD-QA is a multi-choice **HEA**lthcare **D**ataset. The questions come from exams to access a specialized position in the Spanish healthcare system, and are challenging even for highly specialized humans. They are designed by the [Ministerio de Sanidad, Consumo y Bienestar Social](https://www.mscbs.gob.es/), who also provides direct [access](https://fse.mscbs.gob.es/fseweb/view/public/datosanteriores/cuadernosExamen/busquedaConvocatoria.xhtml) to the exams of the last 5 years (in Spanish). 

> Date of the last update of the documents object of the reuse: January, 14th, 2019.

HEAD-QA tries to make these questions accessible for the Natural Language Processing community. We hope it is an useful resource towards achieving better QA systems. The dataset contains questions about the following topics:

- Medicine.
- Nursing.
- Psychology.
- Chemistry.
- Pharmacology.
- Biology.

# Requirements

- Python 3.6.7
- DrQA
- scikit-learn==0.20.2
- numpy==1.16.0
- torch==1.0.0
- torchvision
- spacy==2.0.0
- prettytable==0.70.2

## Requirements for the ARC-Solvers

- Python 3.6.7
- torch==0.3.1
- torchvision
- allennlp==0.20.1

## Installation

We first recommend you to install a virtualenv in the first place (e.g. `virtualenv -p python3.6 head-qa`)
The script `install.sh` automatically installs the mentioned packages, assuming that you have previously created and activated your virtualenv (tested on Ubuntu 18.04, 64 bits). 
The script `install_arc_solvers.sh` install the needed stuff to run the ARC-solvers (Clark et al,2019). 
> We recommend using a different virtualenv for them as stuff such as the pytorch version might create conflicts.

# Datasets

[ES_HEAD dataset](https://drive.google.com/open?id=1dUIqVwvoZAtbX_-z5axCoe97XNcFo1No)
[EN_HEAD dataset](https://drive.google.com/open?id=1phryJg4FjCFkn0mSCqIOP2-FscAeKGV0)
Each dataset contains:
- *.gold -> A tsv gold file that maps question IDs to the ground truth answer ID to such question. One file per exam.
- HEAD[_EN].json -> It contains the whole data for HEAD-QA (used in the so-called 'unsupervised' setting).
- train_HEAD[\_EN].json -> It contains the training set of HEAD-QA (used as the training set in the so-called 'supervised' setting) 
- dev_HEAD[\_EN].json -> A json file containing the development set of HEAD-QA (used in the 'supervised' setting).
- test_HEAD[\_EN].json -> A json file containing the test set of HEAD-QA (used in the 'supervised' setting).

[Data (images, pdfs, etc)](https://drive.google.com/open?id=1a_95N5zQQoUCq8IBNVZgziHbeM-QxG2t). Note that these are medical images and some of them might have sensitive content.



# Run the baselines: Length, Random, Blind_n, IR and DrQA

Available baselines for Spanish HEAD-QA: Length, Random, Blind_n, IR-
Available baselines for English HEAD-QA (HEAD-QA\_EN): Length, Random, Blind_n, IR, DrQA-

**Description of the baselines:**
- Length: Chooses the longest answer
- Random: Chooses a random answer.
- Blind_n: Chooses the *n*th answer.
- IR: Chooses the answer based on the relevance of the query: question+*n*th answer.
- DrQA: A model based on DrQA's (Chen, D., Fisch, A., Weston, J., & Bordes, A. Reading Wikipedia to Answer Open-Domain Questions)


## Creating an inverted index

IR and DrQA require to create an inverted index in advance. This is done using [wikiextractor](https://github.com/attardi/wikiextractor) and following [DrQa's Document Reader](https://github.com/facebookresearch/DrQA/blob/master/scripts/retriever/README.md) guidelines (visit their README.md for a detailed explanation about how to create the index, we here summarize the main steps):

In this work we used the following Wikipedia dumps:

- Spanish: [eswiki-20180620-pages-articles.xml.bz2](http://www.grupolys.org/software/head-qa-acl2019/eswiki-20180620-pages-articles.xml.bz2)
- English: [enwiki-20180701-pages-articles.xml.bz2](http://www.grupolys.org/software/head-qa-acl2019/enwiki-20180701-pages-articles.xml.bz2)

Alternative, you can try to use the current Wikipedia dump maintained by https://dumps.wikimedia.org/

```
PYTHONPATH="$HOME/git/wikiextractor" python $HOME/git/wikiextractor/WikiExtractor.py $PATH_WIKIPEDIA_DUMP -o $PATH_WIKI_JSON --json
PYTHONPATH="$HOME/git/DrQA/" python $HOME/git/DrQA/scripts/retriever/build_db.py $PATH_WIKI_JSON $PATH_DB
PYTHONPATH="$HOME/git/DrQA/" python $HOME/git/DrQA/scripts/retriever/build_tfidf.py --num-workers 2 $PATH_DB $PATH_TFIDF
```

The created model in $PATH_TFIDF it's what will be used as our inverted index. 
If they are of any help, the indexes we used in our work can be found [here](http://www.grupolys.org/software/head-qa-acl2019/wiki-articles.tfidf.zip).

## Updating DrQA's tokenizer

By default, DrQA uses the CoreNLP tokenizer. In this work we used the SpacyTokenizer instead. To use it, go to `DrQA/drqa/pipeline/__init__.py` and make sure you use the DEFAULT below these lines. Also, we used `multitask.mdl` as the `reader_model`. Make sure you have downloaded it when you installed DrQA.

```
from ..tokenizers import CoreNLPTokenizer, SpacyTokenizer

DEFAULTS = {
    'tokenizer': SpacyTokenizer,#CoreNLPTokenizer,
    'ranker': TfidfDocRanker,
    'db': DocDB,
    'reader_model': os.path.join(DATA_DIR, 'reader/multitask.mdl'),
}
```


## Create a configuration file

```
#A configuration file for Spanish

lang=es
eval=eval.py
#Path to your DrQA's installation
drqa=DrQA/ 
use_stopwords=False
ignore_questions=False 
negative_questions=False 
#The folder containing the .gold files
path_solutions=HEAD/ 

es_head=HEAD/HEAD.json #HEAD-QA in json format
#The inverted index that we have previously created.
es_retriever=wikipedia//home/david.vilares/Escritorio/proof-head-qa-code/head-qa/wikipedia/eswiki-20180620-articles.tfidf 

```


After this, you should be abl to run the script `run.py`:

```
python run.py --config configs/configuration$LANG.config --answerer $ANSWERER --output $OUTPUT
```

- `--config` A path to a configuration file (see the folder `configs` for an example)
- `--answerer` A string to indicate what 'answerer' to use. Valid values are [length, random, ir, drqa, blind_n] (n is a number to indicate to take as the right answer the *n*th answer.
- `--output` The path to the file to save the results

# Running the ARC-solvers

We also run the ARC-Solvers used in the ARC challenge (Clark, P., Cowhey, I., Etzioni, O., Khot, T., Sabharwal, A., Schoenick, C., & Tafjord, O. Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge.). To install and run them follow these steps:

1- Follow the [ARC-solvers README.md instructions](https://github.com/allenai/ARC-Solvers) to create a virtualenv, create the index and download the models and resources:

> NOTE that instead of using their ARC_corpus.txt as the inverted index we used again Wikipedia. If you also want to use Wikipedia you need to do two things:
1. Make sure you have downloaded our [Wikipedia corpus](http://www.grupolys.org/software/head-qa-acl2019/WikiCorpus.zip) in txt format.
2. Modify the file ARC-Solvers/scripts/download_data.sh and change the argument specifying the corpus ARC_corpus.txt to the path where you have stored the Wikipedia corpus.

>NOTE 2 ARC-Solvers need of elasticsearch 6+ to download the data. Download it and to run it execute.
```
cd elasticsearch-<version>
./bin/elasticsearch  
```

2 - Convert HEAD_EN.json into the input format for the ARC solvers

```
PYTHONPATH=. python scripts/head2ARCformat.py --input HEAD_EN/HEAD_EN.json --output HEAD_ARC/
```

3 - Run the models using the evaluation scripts provided together with the ARC solvers:

```
cd ARC-Solvers
sh scripts/evaluate_solver.sh ../HEAD_ARC/HEAD_EN.arc.txt data/ARC-V1-Models-Aug2018/dgem/
sh scripts/evaluate_solver.sh ../HEAD_ARC/HEAD_EN.arc.txt data/ARC-V1-Models-Aug2018/decompatt/
sh scripts/evaluate_bidaf.sh ../HEAD_ARC/HEAD_EN.arc.txt data/ARC-V1-Models-Aug2018/bidaf/
```

4 - Compute the scores for HEAD-QA, based on the ARC-solvers outputs

```
cd ..
python evaluate_arc_solvers.py --arc_results $PATH_RESULTS --output $PATH_OUTPUT_DIR --disambiguator length --breakdown_results --path_eval eval.py
```
where:
- `--arc_results` Path to the output directory containing the outputs computed in step 3.
- `--output` The path to the output directory where to store the results.
- `--disambiguator` The strategy to decide the right answer if many answers where selected as valid by an ARC-solver
- `--breakdown_results` Activate to report individual results for each exam
- `--path_eval` Path to the evaluation script


#### Issues

We had problems running some models, being unable to find the `question-tuplizer.jar` used in the ARC-solvers. If you experience this error `Error: Unable to access jarfile data/ARC-V1-Models-Feb2018/question-tuplizer.jar` we recommend you to change in the file `scripts/evaluate_solver.sh` the line:
`java -Xmx8G -jar data/ARC-V1-Models-Feb2018/question-tuplizer.jar`
by
`java -Xmx8G -jar data/ARC-V1-Models-Aug2018/question-tuplizer.jar`

We also had problems ruuning the dgem baseline. The default torch version that is installed if you follow the instructions in the ARC-solvers README.md is the 0.4.1. To make them work we needed to install torch 0.3.1 instead.

## Acknowledgements

This work has received funding from the European Research Council (ERC), under the European Union's Horizon 2020 research and innovation programme (FASTPARSE, grant agreement No 714150).

### References

Vilares, David and Gómez-Rodríguez, Carlos. "HEAD-QA: A Healthcare Dataset for Complex Reasoning", to appear, ACL 2019.
