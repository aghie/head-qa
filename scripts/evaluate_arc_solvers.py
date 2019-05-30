from argparse import ArgumentParser
from subprocess import PIPE,Popen
from utils import *
from models import LengthAnswerer, BlindAnswerer
from collections import OrderedDict
import os
import json
import tempfile
import subprocess
import utils
import sys


def disambiguate(qa,disambiguator, d):
    
    if disambiguator:
        
        if disambiguator.lower() == "length":
            return d["length"].predict([qa])[1]-1

        elif disambiguator.lower() == "blind":
            #We select as the right answer to choice located before the last one
            return len(qa[2])-1
    else:
        return 
        

def breakdown_output(l):
    """
    Args 
    l (string) A list of tuples (exam, questionid, answerid). Id must follow the format $BASENAME_$NAMEEXAM_$QID
    """      
    
    def parse_questionid(name):
        
        try:
            exam = name.rsplit("_",1)[0]
            qid = name.rsplit("_",1)[1]    
            return exam, qid
        except IndexError:
            raise ValueError("The variable 'name' does not respect the format")
    
    d = OrderedDict()
    for questionid, answer in l:
        
        exam, qid = parse_questionid(questionid)
        
        if exam not in d:
            d[exam] = OrderedDict()
        if qid not in d[exam]:
            d[exam][qid] = answer
        else:
            raise KeyError("Key", qid,"already exists in dictionary")
    return d


def _select_answer(line_json):
    
    selected_answers = line_json["selected_answers"].split(",")
    #An ARC solver, we need to disambiguate
    if len(selected_answers) > 1:
#        print ("MORE than one answer selected")
#        print ("line_json", line_json)
        qa = (1,"", [choice["text"] for choice in line_json["question"]["choices"]
                                                                   if choice["label"] in selected_answers])
#        print ("options", qa)
        iselected = disambiguate(qa, args.disambiguator, disambiguators)
#        print ("iselected", iselected)
#        input("NEXT")
        return selected_answers[iselected]
    else:
#         print ("ONLY one answer selected")
#         print ("line_json", line_json)
#         print ("selected_answer", line_json["selected_answers"])
#         input("NEXT")
        return line_json["selected_answers"]
    
    
def _select_negative_answer(line_json):
    
    score = sys.maxsize
    answer = utils.ID_UNANSWERED
    

    for choice in line_json["question"]["choices"]:    
        if score > choice["score"]:
            answer = choice["label"]
            score = min(score, choice["score"])
#            print ("score", score)
#    print ("answer", answer)
#    input("NEXT")
    return answer
    

# def all_scores_are_zero(line_json):
#     
#     return not any([1 for choice in line_json["question"]["choices"] 
#                 if choice["score"] != 0])


def select_answer(line_json, ignore, negative,
                  qclassifier):
    
    if ignore:    
        if (qclassifier is not None and qclassifier.is_unanswerable(line_json["question"]["stem"])
            ):
            return utils.ID_UNANSWERED 
        else:
            if not negative:
                return _select_answer(line_json)
            else:
                return _select_negative_answer(line_json)            
    else:
        if not negative:
            return _select_answer(line_json)
        else:
            return _select_negative_answer(line_json)
        
        

if __name__ == '__main__':
    
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--arc_results", dest="arc_results", 
                            help="Path to the directory containing the ARC results")
    arg_parser.add_argument("--output", dest="output",
                            help="Path to the output file where to store the results")
    arg_parser.add_argument("--disambiguator", dest="disambiguator", default=None,
                            help="Backup answerer to use if an ARC solver returns multiple questions [LengthAnswerer, BlindAnswerer]")
    arg_parser.add_argument("--breakdown_results", dest="breakdown_results", action="store_true",
                            help="To breakdown results for each exam (each JSON 'question' field must include both an 'exam' and a 'qid' fields")
    arg_parser.add_argument("--ignore_questions", dest="ignore_questions",
                            help="To ignore questions according to the strategy described in the paper", action="store_true")
    arg_parser.add_argument("--negative_questions", dest="negative_questions",
                            help="It deals with negative questions", action="store_true")
    arg_parser.add_argument("--path_eval",
                            help="Path to head-qa/eval.py")
    args = arg_parser.parse_args()

    results_files = [args.arc_results+os.sep+file 
                     for file in os.listdir(args.arc_results)
                     if "qapredictions" in file]
    
    
    neg_words = utils.NEGATION_WORDS_EN
    unanswerable_sentences =  [utils.BOS_IMAGE_QUESTION_EN]
    
    if not args.negative_questions:
        neg_words = []
    if not args.ignore_questions:
        unanswerable_sentences = []
    
    qclassifier = QuestionClassifier(unanswerable= unanswerable_sentences, 
                                     neg_words = neg_words)    
    
    length_answerer = LengthAnswerer()
    disambiguators = {"length": length_answerer}
    scorer = Score()
    for file in results_files:
        
        name_dataset =  file.split("qapredictions")[0].rsplit("/",1)[1]
        name_model = file.split("qapredictions")[1].split("_")[1]

        gold = []
        pred = []
        ids = []
        
        with open(file) as f:
            
            line = f.readline()
            while line != "":
                
                line_json = json.loads(line)
                line = f.readline()
                id = line_json["id"]
                ids.append(id)
                gold.append(line_json["answerKey"])
                pred.append(select_answer(line_json, args.ignore_questions, 
                              args.negative_questions, qclassifier))
                
        
        
        if args.breakdown_results:
            
            assert(len(ids)==len(gold))
            assert(len(ids)==len(pred))
            d_gold = breakdown_output(zip(ids, gold))
            d_pred = breakdown_output(zip(ids, pred))

            for exam in d_gold:
                gold_file = args.arc_results+os.sep+exam+".arc_gold"
                with open(gold_file,"w") as f_gold:      
                    f_gold.write("\n".join( [qid+"\t"+d_gold[exam][qid] 
                                             for qid in d_gold[exam] ]))
                    
                pred_file = args.arc_results+os.sep+exam+".arc_pred" 
                with open(pred_file,"w") as f_pred:      
                    f_pred.write("\n".join([qid+"\t"+d_pred[exam][qid] 
                                            for qid in d_pred[exam] ]))
                
                
                command = ["python",args.path_eval,"--gold",gold_file,"--predicted",pred_file]
               # command = ["python","../eval.py","--gold",gold_file,"--predicted",pred_file]
                p = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, shell=True)
                out, err = p.communicate()
                exam_scores = scorer.parse_eval(out.decode("utf-8"))
                scorer.add_exam(exam, exam_scores)
                
        else:        
            assert(len(id)==len(gold))
            assert(len(id)==len(pred))         
            gold_file = args.arc_results+os.sep+name_dataset+".arc_gold"
            with open(gold_file,"w") as f_gold:      
                f_gold.write("\n".join( [id+"\t"+p for id, p in zip(ids,gold) ]))
                
            pred_file = args.arc_results+os.sep+name_dataset+".arc_pred" 
            with open(pred_file,"w") as f_pred:      
                f_pred.write("\n".join( [id+"\t"+p for id, p in zip(ids,pred) ]))
            
            command = ["python",args.path_eval,"--gold",gold_file,"--predicted",pred_file]
            p = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, shell=True)
            out, err = p.communicate()
    
            exam_scores = scorer.parse_eval(out.decode("utf-8"))
            scorer.add_exam(name_dataset, exam_scores)
    
        print (args.output+os.sep+"EN-"+name_model+"ign="+str(args.ignore_questions)+".neg="+str(args.negative_questions))
        with codecs.open(args.output+os.sep+"EN-"+name_model+"ign="+str(args.ignore_questions)+".neg="+str(args.negative_questions)+".ARC.results","w") as f_out_results:
            f_out_results.write(scorer.get_table().get_string())          

    
    