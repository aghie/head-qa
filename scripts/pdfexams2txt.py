#!/usr/bin/env python
# -*- coding: utf-8 -*-


from argparse import ArgumentParser
import codecs
import os
import json
import tempfile


VERSION = "1.0"
LANGUAGE = "es"

class ExamInfo(object):

    def __init__(self):

        self.pdf = None
        self.answers = None
        self.images = None        


def exam_2_txt(path_pdf, path_txt):    
    """
    Executes pdftotext to extract the raw text from a PDF file.
    The option -layout is used to maintain the two columns format of the exam,
    which simplifies post-processing
    
    Args
    
    path_pdf (string): Path to the exam in PDF format
    path_txt (string): Path to the output path to store the file in raw format
    
    """
    os.system(" ".join(["pdftotext -layout",path_pdf,path_txt]))


def preprocess_line(line, mid):
    """
    Preprocesses a line and infers the text that belongs to the first and second 
    columns.
    
    Args
    
    line (string): A line from the exam
    mid (int): Index where the second column is considered to start
    
    """
    
    if len(line) <= mid+4:
        col1 = line[0:mid+4].strip()
        col2 = ""
    else:
        col1 = line[0:mid+4].strip() if line[0:mid+4] != " "*(mid+4) else ""
        col2 = line[mid+4:].strip()
    return col1, col2


def is_new_element(phrase,cur):
    
    """
    Here, an exam represents: (1) a question or (2) one of the answers.
    These can be easily determined because of the format of the ID.
    """
    
    phrase_aux = phrase.strip().split(". ")
    if len(phrase_aux) > 1:
        #TODO: This is a bit of a mess, but the processing from the pdf is not easy.
        #To "ensure it is an ID at the beginning of the sentence. 
        return phrase_aux[0].isdigit() and ( phrase_aux[0] in ["1","2","3","4","5"]  or len(cur.strip()) == 0
                                             or (len(cur.strip()) != 0 and (cur.strip()[-1] in [".",":","?"]) ) ) 
    
    return False

def concat_element(cur,to_append):

    """
    
    Args:
    
    cur (string): Part of the current element (a question or an answer)
    that we have processed
    to_append (string): Line that we are processing now
    
    """

    #is_new_element estimates if we have finised processing the current
    #question or element
    if is_new_element(to_append, cur):
        
        return cur+"\n"+postprocess_phrase(to_append)
    else:
        return cur+postprocess_phrase(to_append)

    

def postprocess_phrase(phrase):
    """
    Some words might be 'cut' for an exam, as the text might take
    several lines. If we find that the last element of a sentence is
    '-', we remove it, and the word will continue in the next line. 
    Otherwise, we are sure it is the end of a word.
    
    Args:
    
    phrase (string)
    
    Warnings:
    
    This implementation is specific for Spanish
    """
    
    if len(phrase) == 0: return phrase
    
    if phrase[-1] == "-":
        return phrase[:-1]
    else:
        return phrase+" "

    
def contains_all_answers(qas, n_answers):
    """
    Checks if we have identified all the answers for our tuple (Q,A1,A2,A3,A4)
    
    Args:
    
    qas: A tuple of the form (Q,A1,A2,A3,A4). Each exam is a string
    n_answers: Number of expected answers
    """
    
    all = True
     
    for i in range(1,n_answers+1):
        all = all and qas[i].startswith(str(i)+".")

    return all
    
    
def _remove_ids(elements):
    """
    We remove the question and answer ids from the text (they are noise for the input) 
    prior to convert the corpus to JSON
    """
    new_elements = []
    for e in elements:
        new_elements.append(e.split(".",1)[1].strip())
        
    return new_elements


def format_txt_exam(path_text):
    
    """
    Transforms an exam in text format (as processed by exam_2_text) into a list (Q,A1,...,AN).

    Args:
    
    path_text (string): Path to an exam in text format

    """
    
    first_page = True
    col1 = ""
    col2 = ""
    
    qas = []
    pages = ""
    
    #Get the indexes of the footnote pages to know where columns should
    #be split
    d_pages_indexes = {}
    with codecs.open(path_text) as f:
        n_page = 1
        line = f.readline()
        while line != "":
            if line.strip().strip("-").isdigit() or line.strip().replace("-","").replace(" ","").isdigit(): 
                d_pages_indexes[n_page] = line.index(line.strip())
                n_page+=1
            line = f.readline()
         
    with codecs.open(path_text) as f:
        
        line = f.readline()
        n_page=1
        while line != "":
            
            #Beginning of a new page
            if line.strip() == "-1-" or line.strip() == "- 1 -":
                n_page+=1
                first_page = False
                c1, c2 = "",""
                col1 = ""
                col2 = ""
            
            elif line.strip().strip("-").isdigit() or line.strip().replace("-","").replace(" ","").isdigit():
                
                pages += col1+col2    
                
                col1 = ""
                col2 = ""
                n_page+=1
             
            elif not first_page:
                if n_page not in d_pages_indexes: break
                c1,c2 = preprocess_line(line, d_pages_indexes[n_page])
                col1 = concat_element(col1,c1)
                col2 = concat_element(col2,c2)
            line = f.readline()



    pages_split = pages.strip().split("\n")
    n_answers = int(pages_split[-1].split(".")[0])
    j = 1+n_answers
    for i in range(0,len(pages_split),j):
        
        if not contains_all_answers(pages_split[i:i+j], n_answers=n_answers):
            raise ValueError("The sample does not contain all the expected answers")
        
        qas.append(_remove_ids(pages_split[i:i+j]))

    return qas


def format_txt_answers(path):
    """
    Converts the text file with the gold answers into a list of tuples
    (question_id, right_answer_id)

    Args
    
    path (string): Path the text file containing the gold answers

    """

    with codecs.open(path) as f:
        lines = f.readlines()
        
    head_line = lines[0]
    content_lines = lines[1:]
    
    d_columns = {}
    d_columns_content = {}
    
    for j,key in enumerate(head_line.split()):
        if key not in d_columns:
            d_columns[key] = []
            d_columns_content[key] = []
        d_columns[key].append(j)
    
    RC_key = "RC"
    v_keys = [key for key in d_columns if key.startswith("V")]
    v_keys.sort(reverse=True)
    V_key = v_keys[0]
    
    v_rc_indexes = zip([index for index in d_columns[V_key]], [index for index in d_columns[RC_key]]) 
    
    template =[]
    for iv,irc in v_rc_indexes:
        #print iv,irc, content_lines[0].split(), len(content_lines[0].split())
        question_ids = [line.split()[iv] for line in content_lines]  
        answer_ids = [line.split()[irc] for line in content_lines]  
        
        if len(question_ids) != len(answer_ids):
            raise ValueError("question_ids and answer_ids vectors should have the same length, but they do not")
        else:
            template.extend(zip(question_ids, answer_ids))

    return template


def get_image_path(path):
    """
    Args
    
    path(string): Gets a dictionary that maps an image name to its 
    relative path
    """
    
    images = [(path+os.sep+img,img) 
              for img in os.listdir(path)]
    d = {}
    for image_path,name in images:
        abbr = name.split("-")[-1].split(".")[0].replace("img","")
        d[abbr] = "./data"+image_path.split("/data")[1]
    
    return d

def corpus_to_json(qas, template, images, path):
    """
    
    Args:
    
    qas:
    template:
    images:
    path:
    
    """
    
    data = {}
    data["name"] = path.rsplit("/",1)[1]
    data["data"] = []
    
    map_category = {"B": "biology",
             "M": "medicine",
             "E": "nursery",
             "F": "pharmacology",
             "P": "psychology",
             "Q": "chemistry",
             }


    if len(qas) != len(template):
        raise ValueError("qas and template vectors should have the same length, but they do not", len(qas), len(template))
    else:   
        for question_answer, rc in zip(qas, template):
            qid = rc[0]
            qtext = question_answer[0]
            right_answer = rc[1]
            
            if not right_answer.isdigit():
                continue
            
            image= ''
            if qtext.startswith("Pregunta vinculada a la imagen nº"):
                n_image = qtext.replace("Pregunta vinculada a la imagen nº","").split()[0]
                image = images[n_image]
            
            #Obtaining the information from the answers
            answers = []
            for ianswer, answer in enumerate(question_answer[1:],1):
                answers.append({"aid":ianswer,
                                "atext": answer})
            
            data["data"].append({"qid": qid,
                                 "qtext": qtext,
                                 "ra": right_answer,
                                 "answers": answers,
                                 "image": image,
                                 })
            data["category"] = map_category[path[-1]]
            data["year"] = path.rsplit("/",1)[1].split("_")[1]

    return {path.rsplit("/",1)[1]:data}
            

###############################################################################
#                                PDFEXAMS2TXT.PY                              #
###############################################################################
if __name__ == '__main__':
    
    arg_parser = ArgumentParser()


    arg_parser.add_argument("--data", dest="data", 
                            help="Path to the directory containing the different files", default=None)

    arg_parser.add_argument("--output", dest="output", 
                            help="Path to the output directory containing the files", default=None)

    
    args = arg_parser.parse_args()
    
    healthcare_categories = [args.data+os.sep+subdir 
                             for subdir in os.listdir(args.data)]
    
    dict_exams = {}
    data_exams = {}
    dict_solutions = {}
    for category in healthcare_categories:
        files = [category+os.sep+f for f in os.listdir(category)]
        
        for f in sorted(files):
            
            if "1_R" in f:
                print (f)
                continue

            name = f.rsplit("/",1)[1]
            info = name.rsplit(".",1)[1]
            name = name.rsplit(".",1)[0]
            
            if name not in dict_exams:
                dict_exams[name] = ExamInfo()
            
            if info == "pdf":
                dict_exams[name].pdf = f
            elif info == "answers":
                dict_exams[name].answers = f
            elif info == "images":
                dict_exams[name].images = f
            else:
                raise ValueError("Extension of the file is not recognized")
 
    for name_exam in sorted(dict_exams.keys()):

        if dict_exams[name_exam].pdf is None or dict_exams[name_exam].answers is None:
            raise ValueError("pdf or answers attributes from ExamInfo() object ",name_exam," are None")

        aux_file = tempfile.NamedTemporaryFile()
    
        exam_2_txt(dict_exams[name_exam].pdf, aux_file.name)
        exam = format_txt_exam(aux_file.name)
        
        template = format_txt_answers(dict_exams[name_exam].answers)
        dict_solutions[name_exam] = template
        images = None
        if dict_exams[name_exam].images is not None:
            images = get_image_path(dict_exams[name_exam].images)
        
        data_exam = corpus_to_json(exam, template, images, args.output+os.sep+name_exam)
        data_exams.update(data_exam)       
        print ("The exam has been temporarily dumped into", args.output+os.sep+name_exam+".json")

    data = {}
    data["version"] = VERSION 
    data["language"] = LANGUAGE 
    data["exams"] = data_exams
    
    #The corpus formatted as a JSON
    with codecs.open(args.output+"HEAD.json", 'w') as outfile:  
        json.dump(data, outfile)
         
    #A file containing pairs (question_id, right_answer_id). For evaluation purposes
    #If ra is X, then the question was deleted by the committee. We set it to 0
    for exam in dict_solutions:
        with codecs.open(args.output+exam+".gold","w") as f_gold:
            for qid, ra in dict_solutions[exam]:
                if not ra.isdigit():
                    continue
                f_gold.write( "\t".join([qid, ra])+"\n" ) 
                
                