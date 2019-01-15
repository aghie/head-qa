from argparse import ArgumentParser
import codecs
import json
import copy
import os
from utils import Dataset

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
    
    for exam in exams:
        with codecs.open(args.output+os.sep+exam+".drqa.txt","w") as f:         
            data_exam = exams[exam]["data"]
            for ielement, element in enumerate(data_exam):
                data = {}
                question = element["qtext"]
                question_id = element["qid"]
                right_answer = element["answers"][int(element["ra"])-1]["atext"]
                data["question"] = question
                data["qid"] = question_id
                data["answer"] = right_answer
            
                repr = json.dumps(data)
                f.write(repr+"\n")
            