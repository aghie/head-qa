from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
from drqa import retriever
from nltk.corpus import stopwords
import logging
import random
import itertools
import prettytable
import numpy as np
import sys
import utils
import codecs


# class VotingAnswerer(object):
#     
#     def __init__(self, answerers=[]):
#         self.answerers = answerers
#         self.question_classifier = utils.QuestionClassifier()
#         
#     def add(self,answerer):
#         self.answerers.add(answerer)
#         
#     def remove(self, answerer):
#         self.answerers.remove(answerer)
#         
#     def predict(self, qas):
#         preds = []
#             
#         answers = np.zeros((len(self.answerers), len(qas)), dtype=np.integer)
#         for j,answerer in enumerate(self.answerers):
#             answers[j]= [raid for qid, raid in answerer.predict(qas)]
#         
#         print (answers, answers.shape)
#         
#         for qid,i in enumerate(range(0, answers.shape[1]),1):
# 
#             preds.append((str(qid),np.argmax(np.bincount(answers[:,i]))))
# 
#         
#         return preds



class LengthAnswerer(object):
    """
    A solver that selects as the right answer the longest one
    """
    
    NAME = "LengthAnswerer"
    MAX_CRITERIA = "max"
    MIN_CRITERIA = "min"
    
    def __init__(self, criteria=MAX_CRITERIA,count_words=False):
        """
        
        Args
        
        criteria (string). Criteria to choose the right answer based on their lengths. 
        Valid values are "max" or "min"
        count_words (boolean): If True, we split the text and count the number of actual words. 
        Otherwise we simply count the length of the string
        
        """
        
        self.count_words = count_words
        
        if criteria.lower() == self.MAX_CRITERIA:
            self.criteria = max
        elif criteria.lower() == self.MIN_CRITERIA:
            self.criteria = min
        else:
            raise NotImplementedError
    
    def name(self):
        return self.NAME
    
    def predict(self, qas):
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (Q, A1,...,AN)
        
        """
        
        preds = []
        for qid, question, answers in qas:
            
            if not self.count_words:
                answer_lengths = list(map(len, answers))
                pred = answer_lengths.index(self.criteria(answer_lengths))+1
            else:
                answer_lengths = list(map(len, [a.split() for a in answers]))
                pred = answer_lengths.index(self.criteria(answer_lengths))+1
            preds.append((qid, pred))
        return preds


class RandomAnswerer(object):
    """
    A solver that select as the right answer a random one
    """

    NAME = "RandomAnswerer"
    
#     def __init__(self):
#         self.question_classifier = utils.QuestionClassifier()

    def name(self):
        return self.NAME

    def predict(self, qas):        
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (Q, A1,...,AN)
        
        """
        
        preds = []
        for qid, question, answers in qas:
            preds.append((qid,random.randint(1,len(answers))))
        return preds



class WordSimilarityAnswerer(object):
    """
    This solver: (1) computes a question vector by summing the individual embeddings
    of its words (2) repeats the same process for each answer and (3) chooses as the right
    answer the asnwer that maximizes cosine_similarity(question_vector, answer_i_vector)
    """

    NAME = "WordSimilarityAnswerer"

    def __init__(self, path_word_emb):
        
        """
        
        Args
        
        path_word_emb (string): Path to the embeddings file
        """
        
        self.word2index = {}
        
        with codecs.open(path_word_emb) as f:
            self.n_words, self.embedding_size = tuple(map(int,f.readline().strip("\n").split()))
            self.word_embeddings = np.zeros(shape=(self.n_words,self.embedding_size), 
                                            dtype=float)
            line = f.readline()
            idl = 0
            while line != "":
            
                word, vector = line.split()[0],  line.split()[1:]
                self.word2index[word] = idl
                self.word_embeddings[idl] = list(map(float,vector))   
                line = f.readline() 
                idl+=1        
            print (" [OK]")
        
        
    def name(self):
        return self.NAME

    def predict(self,qas):
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (Q, A1,...,AN)
        
        """
        
        preds = []
        for qid, question, answers in qas:
        
            question_word_embs = [self.word_embeddings[self.word2index[word]] 
                               if word in self.word2index else np.zeros(self.embedding_size) 
                               for word in question]
            
            embedding_question = normalize(np.sum(question_word_embs, axis=0).reshape(1, -1))
  
            best_score = -1
            for aid, answer in enumerate(answers,1):
                answer_word_embs = [self.word_embeddings[self.word2index[word]] 
                               if word in self.word2index else np.zeros(self.embedding_size) 
                               for word in answer]
                answer_vector = normalize(np.sum(answer_word_embs, axis=0).reshape(1, -1))
                score = cosine_similarity(embedding_question, answer_vector)[0][0]
                if score > best_score:
                    best_answer,best_score = aid, score             
                
            preds.append((qid,best_answer))
        return preds



class IRAnswerer(object):
    
    """
    A solver that select as the right answer the answer that maximized
    the TF-IDF score of a Wikipedia document when the question+answer_i
    is used as the query. It not found it can choose between not to answer 
    or answer randomly.
    
    This implementation uses the IR system presented in DrQa (Chen et al., 2017)
    """

    
    NAME = "IRAnswerer"

    def __init__(self,tfidf_path, always_answer=False, 
                 stopwords =stopwords.words("spanish"),
                 negation_words= utils.NEGATION_WORDS,
                 q_classifier = None):
        
        self.ranker =retriever.get_class('tfidf')(tfidf_path=tfidf_path)
        #self.doc_retriever = retriever.DocDB(db_path=db_path)
        #self.doc_retriever = retriever.DocDB(db_path="/tmp/dumb_json_example2.db")
        self.always_answer = always_answer
        self.stopwords = stopwords
        self.negation_words = negation_words
        self.q_classifier = q_classifier

    def name(self):
        return self.NAME

    def _process(self,query, k=1):
        doc_names, doc_scores = self.ranker.closest_docs(query, k)
       # print (doc_names, doc_scores)
        results = []
        for i in range(len(doc_names)):
            results.append((doc_names[i], doc_scores[i]))
        return results


    def predict(self,qas):
        preds = []
        for qid, question, answers in qas:

            unanswerable = True if self.q_classifier is None else self.q_classifier.is_unanswerable(question)
            f = max
            best_answer, best_score = 0,0
            for neg in self.negation_words:
                if neg in question: 
                    best_answer, best_score = 0, 100000000
                    f = min
                    break            
            
            if not unanswerable:
            
                for aid, answer in enumerate(answers,1):
                    name, score = self._process(" ".join([question, answer]), k=1)[0]   
                    if f == max and score > best_score:
                        best_answer,best_score = aid, score 
                    elif f == min and score < best_score:
                        best_answer,best_score = aid, score
                
            preds.append((qid,best_answer))

        return preds
    

class DrQAAnswerer(object):
    
    def __init__(self):
        pass
    
    
    def predict(self, qas):
        pass