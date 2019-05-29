# HEAD-QA

This repository contains the sources used in "HEAD-QA: A Healthcare Dataset for Complex Reasoning" (ACL, 2019)

### Requirements

Python 3.6.7

### Installation

The script **`install.sh`** automatically installs the mentioned packages, assuming that you have previously created and activated your virtualenv (tested on Ubuntu 18.04, 64 bits). 


### Datasets

[ES_HEAD dataset](https://drive.google.com/open?id=1dUIqVwvoZAtbX_-z5axCoe97XNcFo1No)

[EN_HEAD dataset](https://drive.google.com/open?id=1phryJg4FjCFkn0mSCqIOP2-FscAeKGV0)

[Data (images, pdfs, etc)](https://drive.google.com/open?id=1a_95N5zQQoUCq8IBNVZgziHbeM-QxG2t). Note that these are medical images and some of them might have sensitive content.

HEAD-QA is a multi-choice **HEA**lthcare **D**ataset. The questions come from exams to access a specialized position in the Spanish healthcare system, and are challenging even for highly specialized humans. They are designed by the [Ministerio de Sanidad, Consumo y Bienestar Social](https://www.mscbs.gob.es/), who also provides direct [access](https://fse.mscbs.gob.es/fseweb/view/public/datosanteriores/cuadernosExamen/busquedaConvocatoria.xhtml) to the exams of the last 5 years (in Spanish). 

> Date of the last update of the documents object of the reuse: January, 14th, 2019.

HEAD-QA tries to make these questions accesible for the Natural Language Processing community. We hope it is an useful resource towards achieving better QA systems. The dataset contains questions about the following topics:

- Medicine 
- Nursing
- Psychology
- Chemistry
- Pharmacology
- Biology



### Run the baselines: Length, Random, Blind_n, IR and DrQA

Available baselines for Spanish HEAD-QA: Length, Random, Blind_n, IR

Available baselines for English HEAD-QA (HEAD-QA\_EN): Length, Random, Blind_n, IR, DrQA

**Description of the baselines:**
- Length: Chooses the longest answer
- Random: Chooses a random answer.
- Blind_n: Chooses the *n*th answer.
- IR: Chooses the answer based on the relevance of the query: question+*n*th answer.
- DrQA: A model based on DrQA's (Chen, D., Fisch, A., Weston, J., & Bordes, A. Reading Wikipedia to Answer Open-Domain Questions)


#### Creating an inverted index

IR and DrQA require to create an inverted index in advance. This is done using [wikiextractor](https://github.com/attardi/wikiextractor) and following [DrQa's Document Reader](https://github.com/facebookresearch/DrQA/blob/master/scripts/retriever/README.md) guidelines (visit their README.md for a detailed explanation about how to create the index, we here summarize the main steps):

In this work we used the following Wikipedia dumps:

- Spanish: eswiki-20180620-pages-articles.xml.bz2
- English: enwiki-20180701-pages-articles.xml.bz2

```
PYTHONPATH="$HOME/git/wikiextractor" python $HOME/git/wikiextractor/WikiExtractor.py $PATH_WIKIPEDIA_DUMP -o $PATH_WIKI_JSON --json
PYTHONPATH="$HOME/git/DrQA/" python $HOME/git/DrQA/scripts/retriever/build_db.py $PATH_WIKI_JSON $PATH_DB
PYTHONPATH="$HOME/git/DrQA/" python $HOME/git/DrQA/scripts/retriever/build_tfidf.py --num-workers 2 $PATH_DB $PATH_TFIDF
```

The created model in $PATH_TFIDF it's what will be used as our inverted index.

#### Updating DrQA's tokenizer

By default DrQA uses the CoreNLP tokenizer. In this work we used the SpacyTokenizer instead. To use it, go to `DrQA/drqa/pipeline/__init__.py` and make sure you use this DEFAULT. Also, we used `multitask.mdl` as the `reader_model`. Make your you have downloaded when you installed DrQA.

```
DEFAULTS = {
    'tokenizer': SpacyTokenizer,#CoreNLPTokenizer,
    'ranker': TfidfDocRanker,
    'db': DocDB,
    'reader_model': os.path.join(DATA_DIR, 'reader/multitask.mdl'),
}
```


#### Create a configuration file

```
#A configuration file for Spanish

lang=es
eval=$HOME/git/head-qa/eval.py
drqa=$HOME/git/DrQA/ #Path to your DrQA's installation
use_stopwords=False
ignore_questions=False
negative_questions=False
path_solutions=$PATH_TO_HEAD #The folder containing the .gold files

es_embeddings=$PATH_TO_YOUR_SPANISH_EMBEDDINGS # We used SBW-vectors-300-min5.txt
es_head=$PATH_TO_HEAD/HEAD.json
es_retriever=$PATH_TFIDF

```


After this, you should be able to run the baseline simply use the script `run.py`:

```
python run.py --config configs/configuration$LANG.config --answerer $ANSWERER --output $OUTPUT
```

- `--config` A path to a configuration file (see the folder `configs` for an example)
- `--answerer` A string to indicate what 'answerer' to use. Valid values (lowercased) are [length, random, ir, drqa, blind_n] (n is a number to indicate to take as the right answer the *n*th answer.
- `--output` The path to the file to save the results



#### Running the ARC-solvers

We also tried existing multi-choice system published (Clark, P., Cowhey, I., Etzioni, O., Khot, T., Sabharwal, A., Schoenick, C., & Tafjord, O. Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge.)

(to be filled)

### References

Vilares, David and Gómez-Rodríguez, Carlos. HEAD-QA: A Healthcare Dataset for Complex Reasoning", to appear, ACL 2019.