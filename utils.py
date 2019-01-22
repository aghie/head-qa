from numpy import intersect1d
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from collections import defaultdict, Counter
from prettytable import PrettyTable
import codecs
import json
import string

 
ACCURACY="accuracy"
F1_SCORE = "F1-score"
RECALL = "recall"
PRECISION = "precision"
RIGHT="right"
WRONG="wrong"
UNANSWERED="unanswered"
NETAS="netas"
NEGATION_WORDS_ES = ["NO","FALSA","INCORRECTA","FALSO","INCORRECTO","MENOR","MENOS"]
NEGATION_WORDS_EN = ["NO", "FALSE", "INCORRECT", "LESS"]
BOS_IMAGE_QUESTION_ES = "Pregunta vinculada a la imagen"
BOS_IMAGE_QUESTION_EN = "Question linked to image"
ID_UNANSWERED = 0

def config_file_to_dict(input_file):
    config = {}
    fins = open(input_file,'r').readlines()
    for line in fins:
        if len(line) > 0 and line[0] == "#":
            continue
        if "=" in line:
            pair = line.strip().split('#',1)[0].split('=',1)
            item = pair[0]
            if item in config:
                print("Warning: duplicated config item found: %s, updated."%(pair[0]))
            config[item] = pair[-1]                
    return config


def is_int(token):
    try:
        int(token)
        return True
    except ValueError:
        return False

class QuestionClassifier():
    
    QUESTION_WITH_NEGATION = "NEGATION"
    QUESTION_WITH_STATISTICS = "STATISTICS"
    QUESTION_WITH_IMAGE = "WITH_IMAGE"
    QUESTION_OTHER = "OTHER"
    
    CLASSES = [QUESTION_WITH_NEGATION, 
               QUESTION_WITH_STATISTICS, 
               QUESTION_WITH_IMAGE,
               QUESTION_OTHER]
    
    def __init__(self, unanswerable=[], neg_words=[]):
        
        self.unanswerable = unanswerable
        self.neg_words = neg_words
    
    """
    Preditcs the type of question
    """
    def _predict_type(self, question):
        
        for unans in self.unanswerable:
            if question.startswith(unans):
                return self.QUESTION_WITH_IMAGE
        
        for negation in self.neg_words:
            if negation in question:
                return self.QUESTION_WITH_NEGATION
        
        return self.QUESTION_OTHER
            
    def is_unanswerable(self, question):    
        return self._predict_type(question) in [self.QUESTION_WITH_IMAGE]
    
    def is_reversed_score(self, question):
        return self._predict_type(question) == self.QUESTION_WITH_NEGATION



class TextSimilarity(object):
    """
    It measures the similarity between two texts (percentage of words shared
    between the answer and the span
    """    
    
    def __init__(self, stopwords=stopwords.words('english'),
                 lemmatizer=WordNetLemmatizer()):
        
        self.stopwords = stopwords
        self.lemmatizer = lemmatizer
    
    
    def _preprocess(self, tokens):
        return  [self.lemmatizer.lemmatize(t).lower() for t in tokens 
                 if t.lower() not in self.stopwords and t.lower() not in string.punctuation] 

    def _compute_overlap(self,l1, l2):
        """
        Computes the percentage of elements of l1 that is in l2
        
        Args
        
        l1 (list): A list of strings
        l2 (list): A list of strings
        """
        
        d1 = Counter(l1)
        d2 = Counter(l2)
    
        o1 = 0.
        for k in d1:
            o1 += min(d1[k], d2[k])

        if len(l2) == 0:
            return 0
        return o1 / len(l2)
  

    def similarity(self,tokens1,tokens2):
        
        ptokens1 = self._preprocess(tokens1)
        ptokens2 = self._preprocess(tokens2)   
        return self._compute_overlap(ptokens1, ptokens2) 
        
    

class Score(object):

    iRIGHT = 0
    iWRONG = 1
    iUNANSWERED = 2
    iPRECISION = 3
    iRECALL = 4
    iF1 = 5
    iNETAS = 6


    def __init__(self):
        self.results = {}
        
    def parse_eval(self, output_eval):
        
        prec = 0.0
        recall = 0.0
        f1 = 0.0
        netas = 0.0
        
        d = {}
        for line in output_eval.split("\n"):

            if line.startswith("Number of valid predictions"):
                pass
            elif line.startswith(RIGHT):
                right = line.replace(RIGHT,"")
                d[RIGHT] = right    
            elif line.startswith(WRONG):
                wrong = line.replace(WRONG,"")
                d[WRONG] = wrong   
            elif line.startswith(UNANSWERED):
                unanswered = line.replace(UNANSWERED,"")
                d[UNANSWERED] = unanswered       
            elif line.startswith(PRECISION):
                prec = line.replace(PRECISION,"")
                d[PRECISION] = prec
            elif line.startswith(RECALL):
                recall = line.replace(RECALL,"")
                d[RECALL] = recall
            elif line.startswith(F1_SCORE):
                f1_score = line.replace(F1_SCORE,"")
                d[F1_SCORE] = f1_score
                pass
            elif line.startswith(ACCURACY):
                acc = line.replace(ACCURACY, "")
                d[ACCURACY] = acc
            elif line.startswith(NETAS):
                netas = line.replace(NETAS,"")
                d[NETAS] = netas
                
        return self.scores_to_list(d)

    def scores_to_list(self, dscores):
        return list(map(float,[dscores[RIGHT],dscores[WRONG],dscores[UNANSWERED],dscores[PRECISION],
                dscores[RECALL],dscores[F1_SCORE],dscores[NETAS]]))

    def add_exam(self, exam, scores):
        self.results[exam] = scores
        
    def get_exam_scores(self, exam):
        return self.results[exam]
    
    def get_category_scores(self, category):
        
        category_scores = []
        for exam in self.results:
            if category in exam:
                category_scores.append(self.results[exam])
        return category_scores
    
    def get_average_results(self, exams_scores):
        average = [0]*len(exams_scores[0])
        for exam in exams_scores:
            for index,(s1, s2) in enumerate(zip(average, exam)):
                average[index] = s1+s2
        return [round(e/len(exams_scores),3) for e in average]

    def get_table(self):
        table = PrettyTable()
        table.field_names = ["Exam","Year","Right","Wrong","Unanswered","Precision","Recall","F1-score", "NETAS"]
        
        #Computing individual results
        for exam in self.results:
            e = [exam,""]
            e.extend(self.results[exam])
            table.add_row(e)
        
        #Computing average results per category
        biology_exams = self.get_category_scores("_B")
        if len(biology_exams) != 0:
            biology_scores = self.get_average_results(biology_exams)    
            biology_row = ["Biology (avg)", ""]
            biology_row.extend(biology_scores)
            table.add_row(biology_row)
        
        medicine_exams = self.get_category_scores("_M")
        if len(medicine_exams) != 0:
            medicine_scores = self.get_average_results(medicine_exams)
            medicine_row = ["Medicine (avg)", ""]
            medicine_row.extend(medicine_scores)
            table.add_row(medicine_row)

        nursery_exams = self.get_category_scores("_E")
        if len(nursery_exams) != 0:
            nursery_scores = self.get_average_results(nursery_exams)
            nursery_row = ["Nursery (avg)",""]
            nursery_row.extend(nursery_scores)
            table.add_row(nursery_row)
            
        pharma_exams = self.get_category_scores("_F")
        if len(pharma_exams) != 0:
            pharma_scores = self.get_average_results(pharma_exams)
            pharma_row = ["Pharmacology (avg)", ""]
            pharma_row.extend(pharma_scores)
            table.add_row(pharma_row)
        
        psycho_exams = self.get_category_scores("_P")
        if len(psycho_exams) != 0:
            psycho_scores = self.get_average_results(psycho_exams)
            psycho_row = ["Psychology (avg)", ""]
            psycho_row.extend(psycho_scores)
            table.add_row(psycho_row)
        
        all_scores = self.get_average_results([self.results[exam] for exam in self.results])
        all_row = ["All (avg)", ""]
        all_row.extend(all_scores)
        table.add_row(all_row)
        
        return table

    def _metric_to_index(self, metric):
        if metric == RIGHT: return self.iRIGHT
        if metric == WRONG: return self.iWRONG
        if metric == UNANSWERED: return self.iUNANSWERED
        if metric == PRECISION: return self.iPRECISION
        if metric == RECALL: return self.iRECALL
        if metric == F1_SCORE: return self.iF1
        if metric == NETAS: return self.iNETAS


class Dataset(object):
    
    DATA = "data"
    VERSION = "version"
    EXAMS = "exams"
    
    def __init__(self):
        self.json = None
    
    def load_json(self,path):
        with codecs.open(path) as f:
            self.json = json.load(f)
            
    def get_version(self):
        return self.json[self.VERSION]
    
    def get_exam(self, name_exam):
        return self.json[self.EXAMS][name_exam]
    
    def get_exams(self):
        return self.json[self.EXAMS]
    
    def get_json(self):
        return self.json
    
#     def get_data(self):
#         if self.json is None:
#             raise ValueError("Dataset not provided")
#         
#         return self.json[self.DATA]
    
    def get_qas(self, exam):
        qas = []
        if self.json is None:
            raise ValueError("Dataset not provided")
        
        for sample in self.get_exam(exam)[self.DATA]:
            qas.append((sample["qid"], sample["qtext"], [a["atext"] for a in sample["answers"]]))
        return qas
    
    