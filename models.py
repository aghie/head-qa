from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
from drqa import pipeline
from drqa.retriever import utils
from drqa import retriever
from nltk.corpus import stopwords
from utils import TextSimilarity
import logging
import random
import itertools
import prettytable
import numpy as np
import sys
import utils
import codecs
import tempfile
import subprocess
import json
import os
import abc


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



class Answerer(object):

    def __init__(self,qclassifier):   
        self.qclassifier = qclassifier

    def predict(self, qas):   
        
        not_to_answer = self.not_to_answer(qas)     
        predictions = self._predict(qas)
        for qid in not_to_answer:
            predictions[qid] = utils.ID_UNANSWERED
    
        return predictions    
        
            
    def not_to_answer(self, qas):
        
        unanswerable = []
        for qid, question, answers in qas:
            if self.qclassifier is not None and self.qclassifier.is_unanswerable(question):
                unanswerable.append(qid)
        return unanswerable    
        

    @abc.abstractmethod
    def _predict(self, qas):
        pass


class LengthAnswerer(Answerer):
    """
    A solver that selects as the right answer the longest one
    """
    
    NAME = "LengthAnswerer"
    MAX_CRITERIA = "max"
    MIN_CRITERIA = "min"
    
    def __init__(self, criteria=MAX_CRITERIA,count_words=False,
                 qclassifier=None):
        """
        
        Args
        
        criteria (string). Criteria to choose the right answer based on their lengths. 
        Valid values are "max" or "min"
        count_words (boolean): If True, we split the text and count the number of actual words. 
        Otherwise we simply count the length of the string
        
        """

        Answerer.__init__(self,qclassifier)
        self.count_words = count_words
        
        if criteria.lower() == self.MAX_CRITERIA:
            self.criteria = max
        elif criteria.lower() == self.MIN_CRITERIA:
            self.criteria = min
        else:
            raise NotImplementedError
      
    
    def name(self):
        return self.NAME
    
    def _predict(self, qas):
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (Q, A1,...,AN)
        
        """
        preds = {}
        for qid, question, answers in qas:
            
            if not self.count_words:
                answer_lengths = list(map(len, answers))
                pred = answer_lengths.index(self.criteria(answer_lengths))+1
            else:
                answer_lengths = list(map(len, [a.split() for a in answers]))
                pred = answer_lengths.index(self.criteria(answer_lengths))+1
            preds[qid] = pred
        return preds

    def __str__(self):
        return self.NAME
    


class RandomAnswerer(Answerer):
    """
    A solver that select as the right answer a random one
    """

    NAME = "RandomAnswerer"
    
    def __init__(self, qclassifier=None):
        Answerer.__init__(self,qclassifier)

    def name(self):
        return self.NAME

    def _predict(self, qas):        
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (Q, A1,...,AN)
        
        """
        
        preds = {}
        for qid, question, answers in qas:
            preds[qid] = random.randint(1,len(answers))
        return preds

    def __str__(self):
        return self.NAME
    
    
class BlindAnswerer(Answerer):
    
    NAME = "BlindAnswerer"
    
    
    def __init__(self, default, qclassifier=None):
        
        Answerer.__init__(self,qclassifier)
        self.default = default

    def name(self):
        return self.NAME+"-"+str(self.default)

    def _predict(self, qas):        
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (Q, A1,...,AN)
        
        """
        
        preds = {}
        for qid, question, answers in qas:
            if self.default in range(1,len(answers)+1):
                preds[qid] = self.default
            else:
                raise ValueError("The answer ID",self.default,"is not available in options 1 to ", len(answers))
        return preds    

    def __str__(self):
        return self.NAME+"-"+str(self.default)
    



class WordSimilarityAnswerer(Answerer):
    """
    This solver: (1) computes a question vector by summing the individual embeddings
    of its words (2) repeats the same process for each answer and (3) chooses as the right
    answer the asnwer that maximizes cosine_similarity(question_vector, answer_i_vector)
    """

    NAME = "WordSimilarityAnswerer"

    def __init__(self, path_word_emb, qclassifier):
        
        """
        
        Args
        
        path_word_emb (string): Path to the embeddings file
        """
        
        Answerer.__init__(self,qclassifier)
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

    def _predict(self,qas):
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (QID, Q, A1,...,AN)
        
        """
        
        preds = {}
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
                
            preds[qid] = best_answer
        return preds

    def __str__(self):
        return self.NAME
    


class IRAnswerer(Answerer):
    
    """
    A solver that select as the right answer the answer that maximized
    the TF-IDF score of a Wikipedia document when the question+answer_i
    is used as the query. It not found it can choose between not to answer 
    or answer randomly.
    
    This implementation uses the IR system presented in DrQa (Chen et al., 2017)
    """

    
    NAME = "IRAnswerer"

    def __init__(self,tfidf_path,
                 tokenizer,
                 use_stopwords = False,
                 qclassifier = None):
        
        Answerer.__init__(self,qclassifier)
        self.tokenizer = tokenizer
        self.ranker =retriever.get_class('tfidf')(tfidf_path=tfidf_path)
        self.stopwords = stopwords
        self.use_stopwords = use_stopwords

    def _preprocess(self,query):
        
        if self.use_stopwords:
            return " ".join([token.text for token in list(self.tokenizer(query)) 
                             if not token.is_stop])
        else:
            return " ".join([token.text for token in list(self.tokenizer(query))])            

    def name(self):
        return self.NAME

    def _process(self,query, k=1):
        doc_names, doc_scores = self.ranker.closest_docs(query, k)
        results = []
        for i in range(len(doc_names)):
            results.append((doc_names[i], doc_scores[i]))
        return results


    def _predict(self,qas):
        preds = {}
        for qid, question, answers in qas:

            unanswerable = False if self.qclassifier is None else self.qclassifier.is_unanswerable(question)
            
            #If it is a negation question we look for the least similar answer
            if self.qclassifier.is_negation_question(question):
                best_answer, best_score = 0, 100000000
                f = min     
            else:
                best_answer, best_score = 0,0
                f = max
                
            if not unanswerable:

                question = self._preprocess(question)

                for aid, answer in enumerate(answers,1):
                    name, score = self._process(" ".join([question, answer]), k=1)[0]   
                    if f == max and score > best_score:
                        best_answer,best_score = aid, score 
                    elif f == min and score < best_score:
                        best_answer,best_score = aid, score
                
            preds[qid] = best_answer
        
        return preds

    def __str__(self):
        return self.NAME
        


class DrQAAnswerer(Answerer):
    """
    A solver that implements a simple wrapper to make predictions using 
    DrQA (Chen et al. 2017)
    """
    NAME = "DrQAAnswerer"
    
    def __init__(self, tokenizer, batch_size=64, qclassifier=None):
        
        """
        Args
        
        drqa (string): 
        """
        
        print ("Tokenizer", tokenizer)
        Answerer.__init__(self,qclassifier)
        self.batch_size = batch_size
        self.n_docs = 1
        self.top_n = 1
        self.ts = TextSimilarity()
        self.drqa = pipeline.DrQA(
                    reader_model=None,
                    fixed_candidates=None,
                    embedding_file=None,
                    tokenizer="spacy",
                    batch_size=batch_size,
                    cuda=False,
                    data_parallel=False,
                    ranker_config={'options': {'tfidf_path': None,
                                               'strict': False}},
                    db_config={'options': {'db_path': None}},
                    num_workers=1,
                )

        
    
    def name(self):
        return self.NAME

    def _predict(self, qas):
        """
        
        Returns a list of tuples (question_id, right_answer_id)
        
        Args
        
        qas (list). A list of tuples of strings of the form (QID, Q, A1,...,AN)
        
        """        

        preds = {}
        #preds = []
        queries = [question for qid, question, answers in qas]   
        tmp_out = tempfile.NamedTemporaryFile(delete=False)   
        
        drqa_answers = []
        with open(tmp_out.name, 'w') as f:
            batches = [queries[i: i + self.batch_size]
                       for i in range(0, len(queries), self.batch_size)]
            for i, batch in enumerate(batches):
#                 logger.info(
#                     '-' * 25 + ' Batch %d/%d ' % (i + 1, len(batches)) + '-' * 25
#                 )
                predictions = self.drqa.process_batch(
                    batch,
                    n_docs=self.n_docs,
                    top_n=self.top_n,
                )
                drqa_answers.extend([p[0]["span"] for p in predictions])
        
        #Compare which answer is the closest one to the DrQA answers
        assert (len(drqa_answers) == len(qas))
        for pred_answer, (qid,question,answers) in zip(drqa_answers, qas):
            similarities = sorted([(idanswer, self.ts.similarity(pred_answer.split(" "), answer.split(" "))) 
                                   for idanswer,answer in enumerate(answers,1)], 
                                   key= lambda x : x[1], reverse=True)
            preds[qid] = similarities[0][0] 
        return preds                    


    def __str__(self):
        return self.NAME
    
        

        