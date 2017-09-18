import copy
import os
import pickle
from collections import defaultdict
from parlai.core.dict import DictionaryAgent
from parlai.core.params import class2str


def get_char_dict():
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dict.pcl'), 'rb') as f:
        base_dict = pickle.load(f)
    char_dict = defaultdict(int)
    char_dict.update(base_dict)
    return char_dict


class NERDictionaryAgent(DictionaryAgent):

    @staticmethod
    def add_cmdline_args(argparser):
        group = DictionaryAgent.add_cmdline_args(argparser)
        group.add_argument(
            '--dict_class', default=class2str(NERDictionaryAgent),
            help='Sets the dictionary\'s class'
        )

    def __init__(self, opt, shared=None):
        child_opt = copy.deepcopy(opt)
        # child_opt['model_file'] += '.labels'
        child_opt['dict_file'] = os.path.splitext(child_opt['dict_file'])[0] + '.labels.dict'
        self.labels_dict = DictionaryAgent(child_opt, shared)
        self.char_dict = get_char_dict()
        super().__init__(opt, shared)

    def observe(self, observation):
        observation = copy.deepcopy(observation)
        labels_observation = copy.deepcopy(observation)
        labels_observation['text'] = None
        observation['labels'] = None
        self.labels_dict.observe(labels_observation)
        return super().observe(observation)

    def act(self):
        self.labels_dict.act()
        super().act()
        return {'id': 'NERDictionary'}

    def save(self, filename=None, append=False, sort=True):
        filename = self.opt['model_file'] if filename is None else filename
        self.labels_dict.save(os.path.splitext(filename)[0] + '.labels.dict')
        return super().save(filename, append, sort)

    def tokenize(self, text, building=False):
        return text.split(' ') if text else []

