from models import RandomAnswerer, LengthAnswerer, IRAnswerer, WordSimilarityAnswerer, DrQAAnswerer, BlindAnswerer
from spacy.lang.es import Spanish
from spacy.lang.en import  English
from utils import *
from argparse import ArgumentParser
from subprocess import PIPE,Popen
from tqdm import tqdm
import codecs
import json
import tempfile
import os
import random
import subprocess
import configparser
import utils
import spacy
import en_core_web_sm


SPANISH = "es"
ENGLISH = "en"

if __name__ == '__main__':
    
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--config", dest="config", help="Path to the configuration file")
    arg_parser.add_argument("--output", dest="output", help="Path to the output to store the results")
    arg_parser.add_argument("--answerer", dest="answerer", help="Name of the answerer to be used to train the model")
    
    args = arg_parser.parse_args()
    config = config_file_to_dict(args.config)
    #Load the configuration for Spanish
    path_solutions = config["path_solutions"]
    
    if config["lang"].lower() == SPANISH:
        tfidf_retriever = config["es_retriever"]
        output_dir = config["es_output"]
        path_head =config["es_head"]
    
        unanswerable_sentences = [utils.BOS_IMAGE_QUESTION_ES]
        neg_words = utils.NEGATION_WORDS_ES
        nlp = spacy.load('es_core_news_sm') 
        tokenizer = Spanish().Defaults.create_tokenizer(nlp)
        
    elif config["lang"].lower() == ENGLISH:
        tfidf_retriever = config["en_retriever"]
        output_dir = config["en_output"]
        path_head =config["en_head"]
        unanswerable_sentences = [utils.BOS_IMAGE_QUESTION_EN]
        neg_words = utils.NEGATION_WORDS_EN
        nlp = spacy.load('en_core_web_sm')
        tokenizer = English().Defaults.create_tokenizer(nlp)

    else:
        raise NotImplementedError
    
    ignore_questions = True if config["ignore_questions"].lower() == "true" else False
    negative_questions = True if config["negative_questions"].lower() == "true" else False
    use_stopwords = True if config["use_stopwords"].lower() == "true" else False
    
    random.seed(17)
    unanswerable = []

    if not negative_questions:
        neg_words = []
    if not ignore_questions:
        unanswerable_sentences = []
    
    qclassifier = QuestionClassifier(unanswerable= unanswerable_sentences, 
                                     neg_words = neg_words)    
           
    if args.answerer.lower() == "length":
        answerer = LengthAnswerer(qclassifier=qclassifier)
    elif args.answerer.lower().startswith("blind"):
        x = int(args.answerer.split("_")[1])
        answerer = BlindAnswerer(default=x,qclassifier=qclassifier)
    elif args.answerer.lower() == "random":
        answerer = RandomAnswerer(qclassifier=qclassifier)
    elif args.answerer.lower() == "ir":
        answerer =  IRAnswerer(tfidf_retriever, qclassifier=qclassifier,
                               use_stopwords=False, tokenizer=tokenizer)
    elif args.answerer.lower() == "drqa":
        answerer =  DrQAAnswerer(tokenizer=tokenizer,
                                 qclassifier=qclassifier)
    else:
        raise NotImplementedError("Answerer", args.answerer," is not available")
    
    systems = [answerer]
    solutions =  {f.replace(".gold",""):path_solutions+os.sep+f for f in os.listdir(path_solutions) if f.endswith(".gold")}
    score = Score()
    dataset = Dataset()    
    dataset.load_json(path_head)
    predictions = {}
    unanswerable = {}
    for answerer in systems:
             
        print ("Running ", answerer, "on ", path_head)   
        avg_netas = 0
        avg_fscore = 0

        if answerer not in predictions:
            predictions[answerer.name()] = {}
            unanswerable[answerer.name()] = set([])
        n_exams = len(dataset.get_exams())
        for exam in tqdm(dataset.get_exams()):
            qas = dataset.get_qas(exam)
           # print ("Answerer", answerer, "processing",  exam)
            preds = answerer.predict(qas)
            predictions[answerer.name()][exam] = preds  
             
        
    systems = []
    ir_answerer = None
    for answerer in predictions:
        for exam in predictions[answerer]:
            gold = solutions[exam]
            tmp = tempfile.NamedTemporaryFile(mode="w",delete=False)
            predicted = tmp.name 
            for qid in predictions[answerer][exam]:
                tmp.write("\t".join([qid,str(predictions[answerer][exam][qid])])+"\n")                       
            tmp.close()        
            
            command = ["python",config["eval"],"--gold",gold,"--predicted",predicted]
            p = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, shell=True)
            a, err = p.communicate()
            e = score.parse_eval(a.decode("utf-8"))
            score.add_exam(exam, e)
            os.remove(tmp.name)
        
        with codecs.open(args.output,"w") as f_out_results:
            f_out_results.write(score.get_table().get_string())     

        
        