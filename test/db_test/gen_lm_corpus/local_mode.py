from post_rec.DataSet.LocalDB import getLocalDB
import post_rec
import json
import logging
import argparse
import tqdm
import multiprocessing
from post_rec.Utility.TextPreprocessing import PreprocessPostContent

logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt = '%m/%d/%Y %H:%M:%S',
                    level = logging.INFO)
logger = logging.getLogger(__name__)

def init():
    global preprocessor
    preprocessor=PreprocessPostContent()

def fetchQuestionData():
    questionsData= list(docDB.loadCollection(docDB.questions).values())

    logger.info("loaded: questions({})".format(len(questionsData)))

    return questionsData

def fetchAnswerData():
    answersData= list(docDB.loadCollection(docDB.answers).values())

    logger.info("loaded: answers({})".format(len(answersData)))

    return answersData


def _genCore(doc_ent):
    
    docs=preprocessor.getPlainTxt(doc_ent["Body"])
    
    if "Title" in doc_ent:
        docs.insert(0, doc_ent["Title"])
    
    word_count=0
    words=[]
    for doc in docs:
        w_doc=doc.split()
        word_count+=len(w_doc)
        if word_count> args.maxLength:
            break
    
        words.extend(w_doc)

    doc_str=" ".join(words)
    return doc_str.strip()


def generateContextAnswerCorpusParallel(doc_data):

    cache=[]
    batch_size=args.batch_size
    batches=[doc_data[i:i+batch_size] for i in range(0,len(doc_data),batch_size)]

    workers=multiprocessing.Pool(args.workers, initializer=init)

    file= post_rec.DataPath + "Corpus/" + args.db.lower() + "-lm{}.txt".format(1 if args.answers else 2)
    with open(file,"w") as f:
        for batch_doc in tqdm.tqdm(batches,desc="processing documents multi-progress"):

            for record in workers.map(_genCore,batch_doc):
                if record is not None:

                    cache.append(record+"\n")

            f.writelines(cache)
            f.flush()
            cache.clear()


        workers.close()
        workers.join()


def generateContextAnswerCorpus(doc_data):

    cache=[]
    
    init()
    file= post_rec.DataPath + "Corpus/" + args.db.lower() + "-lm{}.txt".format(1 if args.answers else 2)
    with open(file,"w") as f:
        for record in tqdm.tqdm(doc_data,desc="processing documents"):
            record=_genCore(record)
            if record is not None:
                cache.append(record+"\n")

            f.writelines(cache)
            cache.clear()



def main():
    if not args.answers:
        doc_data=fetchQuestionData()
    else:
        doc_data=fetchAnswerData()

    if args.workers<2:
        generateContextAnswerCorpus(doc_data)
    else:
        generateContextAnswerCorpusParallel(doc_data)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--batch_size', type=int, default=100)

    parser.add_argument('--db', type=str, default="crossvalidated")
    parser.add_argument("--answers",action="store_true")
    parser.add_argument("--maxLength",type=int, default=500)

    parser.add_argument('--workers', type=int, default=10)
    
    args = parser.parse_args()

    docDB=getLocalDB(args.db)

    logger.info("processing db data: {}".format(docDB.name))

    main()
