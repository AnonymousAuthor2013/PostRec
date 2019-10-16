import json
import os
import torch
import random
import tqdm
from torch.utils.data import (DataLoader, RandomSampler, SequentialSampler,
                              TensorDataset)
from post_rec.Utility.processCorpus import CorpusProcessor
from post_rec import AlphaPathLookUp
from post_rec.Utility import getLogger
logger = getLogger(__name__)

    
class InputFeatures(object):
    """A single set of features of data."""

    def __init__(self, input_ids, segment_ids, label_id):
        self.input_ids = input_ids
        self.segment_ids = segment_ids
        self.label_id = label_id

    def dumps(self):
        record={
            "input_ids":self.input_ids,
            "segment_ids":self.segment_ids,
            "label_id":self.label_id
        }
        record=json.dumps(record)
        return record



#for corpus processor
class FeatureProcessor(CorpusProcessor):
    def params(self):
        self.CLS_Token= "[CLS]"
        self.SEP_Token="[SEP]"
        self.Padding_Index=0

        self.label_map = {"duplicate":0,"direct":1,"transitive":2,"unrelated":3}

        self.__default_label="duplicate"

        self.__sp_tokens={ # cls and sep
            "bert":["[CLS]", "[SEP]", 0],
            "xlnet":["<cls>", "<sep>", 4]
        }
    
    def switch_to(self, name="bert"):
            if name not in self.__sp_tokens:
                raise ValueError("none supported  process corpus dest: {}".format(name))

            self.CLS_Token, self.SEP_Token, self.Padding_Index = self.__sp_tokens[name]

    def __init__(self, config_file):
        CorpusProcessor.__init__(self,config_file)
        self.question_len=100
        self.post_len=400
        self.answers=3
        self.max_seq_len=512
        self.cls_last=False

        self.question_len = self.config.question_len
        self.answers = self.config.answers
        self.post_len = self.config.post_len
        self.max_seq_len=self.config.max_seq_len
        self.cls_last=self.config.cls_last
        self.params()
        self.switch_to(self.config.model)

    def _process_question(self, question):
        question_title = " ".join(self.textExtractor.tokenizer.tokenize(question["Title"]))
        question_body= self._getPreprocess(question["Body"], self.question_len)
        question_txt= " ".join([question_title, question_body])

        question_words=self.tokenizer.tokenize(question_txt)[:self.question_len]
        question_words.append(self.CLS_Token)
        return question_words
    
    def _process_post(self, post):
        title = " ".join(self.textExtractor.tokenizer.tokenize(post["Title"]))

        body=self._getPreprocess(post["Body"],self.question_len)

        ans_iter= map(lambda ans: ans["Body"], self._getBestAnswers(post))
        answers=[]
        for _ in range(self.answers):
            try:
                answers.append(
                    next(ans_iter)
                )
            except:
                break

        answers_txt = self._getPreprocess(" ".join(answers), self.post_len)

        post_txt=" ".join([title, body, answers_txt])

        post_words=self.tokenizer.tokenize(post_txt)[:self.post_len ]
        post_words.append(self.CLS_Token)
        return post_words
    
    def _convert_ids(self, words, seg_id):
        token_ids=self.tokenizer.convert_tokens_to_ids(words)
        seg_ids=[seg_id]*len(words)
        return [token_ids, seg_ids]

    def batch_process_core(self, record):
            question, post, label=record["question"], record["post"], record["label"]

            question_words=self._process_question(question)
            if self.cls_last==False:
                question_words.insert(0, self.CLS_Token)
            q_ids, q_segs=self._convert_ids(question_words, 0)

            post_words=self._process_post(post)
            if self.cls_last:
                post_words.append(self.CLS_Token )
            p_ids, p_segs=self._convert_ids(post_words, 1)

            padding_ids=[]
            pad_len=self.max_seq_len-len(q_ids+p_ids)
            padding_ids+=[self.Padding_Index]*pad_len

            feature=InputFeatures(
                input_ids=q_ids+p_ids+padding_ids,
                segment_ids=q_segs+p_segs+padding_ids,
                label_id=self.label_map[label]
            )

            return feature


    def process(self, question, posts):
        #using one question and relevant posts to construct features

        features=[]
        question_words=self._process_question(question)
        if self.cls_last==False:
            question_words.insert(0, self.CLS_Token)
        q_ids, q_segs=self._convert_ids(question_words, 0)

        for post in tqdm.tqdm(posts, desc="processing posts data"):
            post_words=self._process_post(post)
            if self.cls_last:
                post_words.append(self.CLS_Token )
            p_ids, p_segs=self._convert_ids(post_words, 1)

            padding_ids=[]
            pad_len=self.max_seq_len-len(q_ids+p_ids)
            padding_ids+=[self.Padding_Index]*pad_len

            feature=InputFeatures(
                input_ids=q_ids+p_ids+padding_ids,
                segment_ids=q_segs+p_segs+padding_ids,
                label_id=0
            )

            features.append(feature)

        return features


def load_features_from_file(file_path):
    def _process_one_line(line):
        record=json.loads(line)
        input_ids=record["input_ids"]
        segment_ids=record["segment_ids"]
        label_id=record["label_id"]
        feature=InputFeatures(input_ids=input_ids,
                    segment_ids=segment_ids,
                    label_id=label_id)
        return feature

    with open(file_path, "r", encoding="utf-8") as f:
        features=map(lambda line: _process_one_line(line), f)
        features=list(features)

    return features

class FeatureLoader(object):
    def __init__(self, data_folder, batch_size=16):
        super(FeatureLoader, self).__init__()
        self.data_folder=data_folder
        self.files=list(os.listdir(data_folder))
        self.file_iter=iter(self.files)
        self.batch_size=batch_size
        self.mode="train" #

    def reset(self):
        random.shuffle(self.files)
        self.file_iter=iter(self.files)
    def get_next_file(self):
        try:
            file=next(self.file_iter)
        except:
            self.reset()
            return self.get_next_file()
        return file
    
    def load_data(self, data_size=1e+5):
        logger.info("loading data size:{}".format(data_size))
        features=[]
        while len(features)<data_size:
            file=self.get_next_file()
            tmp_features=load_features_from_file(os.path.join(self.data_folder, file))
            features.extend(tmp_features)
        
        all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        all_segment_ids = torch.tensor([f.segment_ids for f in features], dtype=torch.long)
        all_label_ids = torch.tensor([f.label_id for f in features], dtype=torch.long)
        data = TensorDataset(all_input_ids, all_segment_ids, all_label_ids)
        if self.mode=="train":
            sampler = RandomSampler(data)
        else:
            sampler=SequentialSampler(data)

        dataloader = DataLoader(data, sampler=sampler, batch_size=self.batch_size)

        return dataloader