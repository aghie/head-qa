from argparse import ArgumentParser
from subprocess import PIPE,Popen
from utils import *
from models import LengthAnswerer, BlindAnswerer
import os
import json
import tempfile
import subprocess



def disambiguate(qa,disambiguator, d):
    
    if disambiguator:
        
        if disambiguator.lower() == "length":
            return d["length"].predict([qa])[1]-1

        elif disambiguator.lower() == "blind":
            #We select as the right answer to choice located before the last one
            return len(qa[2])-1
    else:
        return 
        


if __name__ == '__main__':
    
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--arc_results", dest="arc_results", 
                            help="Path to the directory containing the ARC results")
    arg_parser.add_argument("--output", dest="output",
                            help="Path to the output file where to store the results")
    arg_parser.add_argument("--disambiguator", dest="disambiguator", default=None,
                            help="Backup answerer to use if an ARC solver returns multiple questions [LengthAnswerer, BlindAnswerer]")
    
    args = arg_parser.parse_args()

    results_files = [args.arc_results+os.sep+file 
                     for file in os.listdir(args.arc_results)
                     if "qapredictions" in file]
    
    length_answerer = LengthAnswerer()
   
    disambiguators = {"length": length_answerer}
    
    for file in results_files:
        
        name_exam =  file.split("qapredictions")[0].rsplit("/",1)[1]
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
                
                selected_answers = line_json["selected_answers"].split(",")
                
                #An ARC solver, we need to disambiguate
                if len(selected_answers) > 1:
                    
                    qa = (1,"", [choice["text"] for choice in line_json["question"]["choices"]
                                                                       if choice["label"] in selected_answers])
                    
                    iselected = disambiguate(qa, args.disambiguator, disambiguators)
                    pred.append( selected_answers[iselected])
                else:
                    pred.append(line_json["selected_answers"])
        
        gold_file = args.arc_results+os.sep+name_exam+".arc_gold"
        with open(gold_file,"w") as f_gold:      
            f_gold.write("\n".join( [id+"\t"+p for id, p in zip(ids,gold) ]))
            
        pred_file = args.arc_results+os.sep+name_exam+".arc_pred" 
        with open(pred_file,"w") as f_pred:      
            f_pred.write("\n".join( [id+"\t"+p for id, p in zip(ids,pred) ]))
        
        scorer = Score()
        command = ["python","../eval.py","--gold",gold_file,"--predicted",pred_file]
        p = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()
            #print ("------------------>",a)

        exam_scores = scorer.parse_eval(out.decode("utf-8"))
        scorer.add_exam(name_exam, exam_scores)

        with codecs.open(args.output+os.sep+name_exam+"."+name_model+".ARC.results","w") as f_out_results:
            f_out_results.write(scorer.get_table().get_string())          

    
    