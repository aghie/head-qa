from models import RandomAnswerer, LengthAnswerer, IRAnswerer, WordSimilarityAnswerer, DrQAAnswerer, BlindAnswerer
from utils import *
from argparse import ArgumentParser
from subprocess import PIPE,Popen
import codecs
import json
import tempfile
import os
import random
import subprocess
import configparser
import utils


SPANISH = "es"
ENGLISH = "en"



if __name__ == '__main__':
    
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--config", dest="config", help="Path to the configuration file")
    
    args = arg_parser.parse_args()
    config = config_file_to_dict(args.config)
    #Load the configuration for Spanish
    if config["lang"].lower() == SPANISH:
        tfidf_retriever = config["es_retriever"]
        output_dir = config["es_output"]
        path_head =config["es_head"]
        embeddings= config["es_embeddings"]
        name_head = "HEAD.json"
        unanswerable_sentences = [utils.BOS_IMAGE_QUESTION_ES]
        neg_words = utils.NEGATION_WORDS_ES
        
    elif config["lang"].lower() == ENGLISH:
        tfidf_retriever = config["en_retriever"]
        output_dir = config["en_output"]
        path_head =config["en_head"]
        name_head = "HEAD_EN.json"
        unanswerable_sentences = [utils.BOS_IMAGE_QUESTION_EN]
        neg_words = utils.NEGATION_WORDS_EN
      #  embeddings = config["en_embeddings"]
    
    random.seed(17)
    unanswerable = []
   # neg_words = []
    qclassifier = QuestionClassifier(unanswerable= unanswerable_sentences, 
                                     neg_words = neg_words)    
    
#     qclassifier = QuestionClassifier(unanswerable= [], 
#                                      neg_words = [])    
    
    random_answerer = RandomAnswerer(qclassifier=qclassifier)
    length_answerer = LengthAnswerer(qclassifier=qclassifier)
    blind_answerer = BlindAnswerer(default=4,qclassifier=qclassifier)
   # word_similarity_answerer = WordSimilarityAnswerer(embeddings, qclassifier=qclassifier)
   # ir_answerer = IRAnswerer(tfidf_retriever, qclassifier=qclassifier)
   # drqa_answerer = DrQAAnswerer(qclassifier=qclassifier)
        
    #systems = [drqa_answerer,length_answerer, random_answerer]
    systems = [blind_answerer]
    exams = {f.replace(".json",""):path_head+os.sep+f for f in os.listdir(path_head) if f.endswith(name_head)}
    solutions =  {f.replace(".gold",""):path_head+os.sep+f for f in os.listdir(path_head) if f.endswith(".gold")}
    
    score = Score()
    dataset = Dataset()    
    dataset.load_json(exams[name_head.replace(".json","")])
    predictions = {}
    unanswerable = {}
    for answerer in systems:
                
        avg_netas = 0
        avg_fscore = 0

        if answerer not in predictions:
            predictions[answerer.name()] = {}
            unanswerable[answerer.name()] = set([])
        n_exams = len(dataset.get_exams())
        for exam in dataset.get_exams():
            qas = dataset.get_qas(exam)
            print ("Answerer", answerer, "processing",  exam)
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
            #print ("------------------>",a)
            e = score.parse_eval(a.decode("utf-8"))
            score.add_exam(exam, e)
            os.remove(tmp.name)
        
        
        with codecs.open(output_dir+os.sep+config["lang"]+"-"+answerer+".results","w") as f_out_results:
            f_out_results.write(score.get_table().get_string())     

        
        