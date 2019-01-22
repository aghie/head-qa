from utils import F1_SCORE, RECALL, PRECISION,ACCURACY, NETAS, RIGHT, WRONG, UNANSWERED
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import accuracy_score
from argparse import ArgumentParser
import codecs



def netas_score(gold, predicted, avg_10best_scores=574.7):
    
    right = 0
    wrong = 0
    unanswered = 0
    brutas_score = 0
    if len(gold) != len(predicted):
        raise ValueError("The gold and predicted vector must have the same length")
    else:
        for g, p in zip(gold, predicted):
       #     print (g,p, type(g), type(p))
            if g == p: 
                right+=1
                brutas_score+=3
            elif p != 0: 
                brutas_score-=1
                wrong+=1
            else:
                unanswered+=1
    return brutas_score, right, wrong, unanswered


def scores(y_pred,y_gold):
    p,r,f1,_ = precision_recall_fscore_support(y_gold, y_pred, average='macro')
    net,right,wrong,unanswered = netas_score(y_gold,y_pred)
    scores = ""
    scores+=PRECISION+"\t"+str(round(p,3))+"\n"
    scores+=RECALL+"\t"+str(round(r,3))+"\n"
    scores+=F1_SCORE+"\t"+str(round(f1,3))+"\n"
    scores+=ACCURACY+"\t"+str(round(accuracy_score(y_gold, y_predicted),3))+"\n"
    scores+=RIGHT+"\t"+right+"\n"
    scores+=WRONG+"\t"+wrong+"\n"
    scores+=UNANSWERED+"\t"+unanswered+"\n"
    scores+=NETAS+"\t"+net+"\n"

if __name__ == '__main__':

    arg_parser = ArgumentParser()
    arg_parser.add_argument("--gold", dest="gold", help="Path to the PDF file", default=None)
    arg_parser.add_argument("--predicted", dest="predicted", help ="Path to the txt file", default=None)
    
    args = arg_parser.parse_args()
    with codecs.open(args.gold) as f_gold:
        gold = f_gold.readlines()
        y_gold = [int(e.split()[1].strip()) for e in gold]
        
    with codecs.open(args.predicted) as f_predicted:
        predicted = f_predicted.readlines()
        y_predicted =  [int(e.split()[1].strip()) for e in predicted]
    
    p,r,f1,_ = precision_recall_fscore_support(y_gold, y_predicted, average='macro')
    net,right,wrong,unanswered = netas_score(y_gold,y_predicted)
    print (PRECISION,round(p,3))
    print (RECALL, round(r,3))
    print (F1_SCORE, round(f1,3))
    print (ACCURACY,round(accuracy_score(y_gold, y_predicted),3))
    print (RIGHT, right)
    print (WRONG, wrong)
    print (UNANSWERED, unanswered)
    print (NETAS, net )
#     print ("y_gold (1)", y_gold.count(1))
#     print ("y_gold (2)", y_gold.count(2))
#     print ("y_gold (3)", y_gold.count(3))
#     print ("y_gold (4)", y_gold.count(4))
#     print ("y_gold (5)", y_gold.count(5))
#     print ("y_gold", y_gold)
#     print ("y_predicted", y_predicted)
#     print ()
#     print ("Per class",precision_recall_fscore_support(y_gold, y_predicted, average=None,labels=[1, 2, 3, 4, 5]))
    
    