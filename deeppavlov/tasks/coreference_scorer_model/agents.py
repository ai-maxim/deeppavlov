"""
Copyright 2017 Neural Networks and Deep Learning lab, MIPT
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os

from parlai.core.agents import Teacher
from .build import build
from . import utils
from ...utils import coreference_utils

class CoreferenceTeacher(Teacher):

    @staticmethod
    def add_cmdline_args(argparser):
        group = argparser.add_argument_group('Coreference Teacher')
        group.add_argument('--language', type=str, default='ru')
        group.add_argument('--predictions_folder', type=str, default='predicts',
                           help='folder where to dump conll predictions, scorer will use this folder')
        group.add_argument('--scorer_path', type=str, default='scorer/reference-coreference-scorers/v8.01/scorer.pl',
                           help='path to CoNLL scorer perl script')
        group.add_argument('--valid_ratio', type=float,
                           default=0.2, help='valid_set ratio')
        group.add_argument('--test_ratio', type=float,
                           default=0.2, help='test_set ratio')

    def __init__(self, opt, shared=None):
        super().__init__(opt, shared)
        self.last_observation = None
        self.id = 'two-step-coref'
        
        if shared:
            raise RuntimeError('Additional batching is not supported')

        build(opt)
        
        self.dt = opt['datatype'].split(':')[0]
        self.datapath = os.path.join(opt['datapath'], 'coreference', opt['language'])
        self.valid_path = None
        self.train_path = None
        self.predictions_folder = os.path.join(self.datapath, opt['predictions_folder'], self.dt)
        self.scorer_path = os.path.join(self.datapath, opt['scorer_path'])

        # in train mode we use train dataset to train model
        # and valid dataset to adjust threshold
        # in valid and test mode we use test dataset
        if self.dt == 'train':
            self.valid_path = os.path.join(self.datapath, 'valid')
            self.train_path = os.path.join(self.datapath, 'train')
        elif self.dt in ['test', 'valid']:
            self.valid_path = os.path.join(self.datapath, 'test')
        else:
            raise ValueError('Unknown mode: {}. Available modes: train, test, valid.'.format(self.dt))

        self.train_documents = [] if self.train_path is None else os.listdir(self.train_path)
        self.valid_documents = [] if self.valid_path is None else os.listdir(self.valid_path)
        self.len = 1
        self.epoch = 0
        self._epoch_done = False

    def act(self):
        self._epoch_done = True
        train_conll = [open(os.path.join(self.train_path, file), 'r').readlines() for file in self.train_documents]
        valid_conll = [open(os.path.join(self.valid_path, file), 'r').readlines() for file in self.valid_documents]
        return {'id': self.id, 'conll': train_conll, 'valid_conll': valid_conll}

    def observe(self, observation):
        self.last_observation = observation
        self.epoch += 1

    def report(self):
        utils.save_observations(self.last_observation['valid_conll'], self.predictions_folder)
        res = coreference_utils.score(self.scorer_path, self.valid_path, self.predictions_folder)
        return {'f1': res['conll-F-1']}

    def reset(self):
        self._epoch_done = False

    def epoch_done(self):
        return self._epoch_done

    def __len__(self):
        return self.len
