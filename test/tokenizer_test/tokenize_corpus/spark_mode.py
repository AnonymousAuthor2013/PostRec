#encoding=utf-8
from post_rec.tokenizers import get_tokenizer
import post_rec
import argparse
import os
from post_rec.Utility import getLogger
logger=getLogger(__name__)

path_map_tokenizers={
    "bert":post_rec.BertBaseUnCased,
    "gpt2": post_rec.GPT2Base,
    "xlnet": post_rec.XLNetBaseCased,
    "roberta":post_rec.RoBertaBase
}

def init():
    global tokenizer
    name= args.tokenizer
    tokenizer=get_tokenizer(path_map_tokenizers[name], name)


def tokenize(text):
    text=text.value
    tokenized_text=tokenizer.tokenizeLine(text)

    return tokenized_text

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument("--tokenizer",type=str,default="bert", choices=["bert", "roberta", "gpt2","xlnet"])
    parser.add_argument("--file",type=str,default="")

    args=parser.parse_args()

    if args.tokenizer not in path_map_tokenizers:
        args.tokenizer="bert"

    inputfile=args.file
    outputfile=inputfile+".tokenized-"+args.tokenizer

    init()
    from pyspark.sql import SparkSession
    spark = SparkSession\
        .builder\
        .appName("tokenize text with "+args.tokenizer)\
        .getOrCreate()

    tokenized=spark.read.text(inputfile).rdd.map(tokenize)

    tokenized.saveAsTextFile(outputfile)
    spark.stop()
