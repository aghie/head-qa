from models import RandomAnswerer, LengthAnswerer, IRAnswerer, WordSimilarityAnswerer, DrQAAnswerer
from utils import *
from argparse import ArgumentParser
import codecs
import json
import tempfile
import os
import random
import subprocess
import configparser
from subprocess import PIPE,Popen


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
    elif config["lang"].lower() == ENGLISH:
        tfidf_retriever = config["en_retriever"]
        output_dir = config["en_output"]
        path_head =config["en_head"]
        name_head = "HEAD_EN.json"
        
   # random_answerer = RandomAnswerer()
   # length_answerer = LengthAnswerer()
   # word_similarity_answerer = WordSimilarityAnswerer(embeddings)
    q_classifier = None#QuestionClassifier(unanswerable=[QuestionClassifier.QUESTION_WITH_IMAGE])
   # ir_answerer = IRAnswerer(tfidf_retriever, q_classifier=q_classifier)
    drqa_answerer = DrQAAnswerer()
        
    #systems = [word_similarity_answerer]#, random_answerer, length_answerer] #word_similarity_answerer]
    #systems = [ir_answerer, random_answerer, length_answerer]
    systems = [drqa_answerer]
    
    #systems = [word_similarity_answerer]
    
    exams = {f.replace(".json",""):path_head+os.sep+f for f in os.listdir(path_head) if f.endswith(name_head)}
    solutions =  {f.replace(".gold",""):path_head+os.sep+f for f in os.listdir(path_head) if f.endswith(".gold")}

    score = Score()
    dataset = Dataset()    
    dataset.load_json(exams["HEAD_EN"])
    predictions = {}
    for answerer in systems:
                
        avg_netas = 0
        avg_fscore = 0

        if answerer not in predictions:
            predictions[answerer.name()] = {}
        n_exams = len(dataset.get_exams())
        for exam in dataset.get_exams():
            qas = dataset.get_qas(exam)
            #print (qas)
            print ("Answerer", answerer, "processing",  exam)
            preds = answerer.predict(qas)
            predictions[answerer.name()][exam] = preds  
            break
        
    systems = []
    ir_answerer = None
    for answerer in predictions:
        for exam in predictions[answerer]:
            gold = solutions[exam]
            tmp = tempfile.NamedTemporaryFile(mode="w",delete=False)
            predicted = tmp.name 
            for qid, aid in predictions[answerer][exam]:
                tmp.write("\t".join([qid,str(aid)])+"\n")         
            tmp.close()        

            command = ["python",config["eval"],"--gold",gold,"--predicted",predicted]
            p = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, shell=True)
            a, err = p.communicate()
            e = score.parse_eval(a.decode("utf-8"))
            score.add_exam(exam, e)
            os.remove(tmp.name)
        
            print ("exam", exam)
            print ("scores" ,e)
        
        
        with codecs.open(output_dir+os.sep+answerer+".results","w") as f_out_results:
            f_out_results.write(score.get_table().get_string())     
        #print (score.pprint())
        
        