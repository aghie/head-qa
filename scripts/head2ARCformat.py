from argparse import ArgumentParser
import codecs
import json
import copy
import os
from utils import Dataset
from collections import OrderedDict

if __name__ == '__main__':
    
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--input", dest="input", 
                            help="Path to the HEAD dataset", default=None)
    arg_parser.add_argument("--output", dest="output", 
                            help="Path to the output directory where to store the exams in a suitable format for DrQa")
    
    args = arg_parser.parse_args()
    
    dataset = Dataset()
    dataset.load_json(args.input)
    exams = dataset.get_exams()
    name_head = args.input.rsplit("/",1)[1].replace(".json","")
    
    with codecs.open(args.output+os.sep+name_head+".arc.txt","w") as f:         
        for exam in exams:        
            data_exam = exams[exam]["data"]
            for ielement, element in enumerate(data_exam):
            
                arc_id = "_".join([exam, str(ielement)]) 
                data = {"id":arc_id}
                stem = element["qtext"]
                question = {"stem": stem}
                question.update({"exam": exam})
                question.update({"qid": ielement})
                arc_answers = []
                for answer in element["answers"]:
                    arc_answers.append({"text":answer["atext"], "label":str(answer["aid"])})
                
                question.update({"choices": arc_answers})
                
                right_answer = str(element["answers"][int(element["ra"])-1]["aid"])
                data.update({"question":question})
                data.update({"answerKey": right_answer})
            
                repr = json.dumps(data)
                f.write(repr+"\n")  


            