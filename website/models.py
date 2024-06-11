from subprocess                     import Popen
from time                           import sleep
from os                             import path, makedirs, listdir, remove
from json                           import load as load_json

from website                        import SUBSETS, FILTERS, MODELS, SECTIONS
from website                        import BINS_DIR, DATA_DIR, JSON_DIR, XLSX_DIR
from website                        import REUSE_DATA
from website.excel_io               import ExcelIO

def run_worker(args : list[str]) -> Popen:
    process = Popen(["python", "-B", "-W ignore", "spawn_worker.py"] + args)
    print(f'Spawned worker [%s]' % (', '.join(args)))
    return process

class PipelineRunner :
    _workers = list()

    def __init__(self, file : str) :
        for dir in [BINS_DIR, JSON_DIR, XLSX_DIR] :
            if not path.exists(dir) :
                makedirs(dir)
            elif not REUSE_DATA :
                for item in listdir(dir) :
                    remove(f'%s/%s' % (dir, item))

        if not path.exists(f'%s/ALL_LABELS.xlsx' % (XLSX_DIR)) or \
            not all([path.exists(f'%s/%s_ALL.xlsx' % (XLSX_DIR, subset)) for subset in SUBSETS]) :
            ExcelIO().read_dataset(file)

    def __del__(self) :
        print(f'Cleaning up PipelineRunner')
        for proc in self._workers :
            if proc.poll() is None :
                proc.terminate()
                proc.wait()
        self._workers = list()

    def run_attr_workers(self, filter : str, model : str = None) -> None :
        files = len(listdir(JSON_DIR))
        fexps = 0
        for subset in SUBSETS :
            if not path.exists(f'%s/AFS_%s_%s.json' % (JSON_DIR, subset, filter)) :
                if model is not None :
                    self._workers.append(run_worker(['DALEX', subset, model]))
                else :
                    self._workers.append(run_worker([filter, subset]))
                fexps +=1

        if fexps > 0 :
            print(f'Waiting for all %s selections to finish' % (filter))
            while (len(listdir(JSON_DIR)) - files) < fexps :
                sleep(10)
            files = len(listdir(JSON_DIR))
            print(f'Finished all %s selections' % (filter))

    def run_attribute_selectors(self) -> None :
        self.run_attr_workers('CFS')
        self.run_attr_workers('HNET')
        for model in MODELS :
            self.run_attr_workers(f'DALEX_%s' % (model), model)

    def run_model_evaluators(self) -> None:
        files  = 0
        for model in MODELS :
            for filter in FILTERS :
                fexps = 0
                for subset in SUBSETS :
                    name = f'%s_%s' % (subset, filter)
                    if filter == 'DALEX' :
                        name = f'%s_%s' % (name, model)

                    if not path.exists(f'%s/%s_%s.json' % (JSON_DIR, model, name)) :
                        self._workers.append(run_worker(["EVALUATE", name, model]))
                        fexps += 1

                if fexps > 0 :
                    print('Waiting for all %s evaluations on %s subset to finish' % (model, subset))
                    while (len(listdir(JSON_DIR)) - files) < fexps :
                        sleep(10)
                    files = len(listdir(JSON_DIR))

class ResultsViewer() :
    def __init__(self) :
        self._attr   = dict()
        self._scores = dict()
        self._dists  = dict()
        self._bayes  = dict()

        self._loading = False

    def is_loading(self) -> bool :
        return self._loading

    def read_results(self) -> None:
        self._loading = True
        self._labels = ExcelIO().load_excel('ALL_LABELS')
        labels  = dict()
        columns = []
        for section, span in SECTIONS.items() :
            with open(f'%s/ALL_%s.txt' % (DATA_DIR, section), 'r') as f :
                labels[section] = f.read().splitlines()
            columns = columns + [f'%s_%i' % (section, (index - span[0])) for index in range(span[0], span[1])]

        for subset in SUBSETS :
            print('Reading selected attributes for %s subset' % (subset))
            attr = dict()
            attr_union = []
            for filter in ['CFS', 'HNET', 'DALEX_RFC', 'DALEX_CNB', 'DALEX_SVM', 'DALEX_LRC'] :
                with open(f'%s/AFS_%s_%s.json' % (JSON_DIR, subset, filter), 'r') as f :
                    attr[filter] = load_json(f)
                    attr_union += list(attr[filter].keys())

            attr['ALL'] = dict()
            attr_union = list(set(attr_union))
            for attr_ in list(columns) :
                if attr_ in attr_union :
                    group = attr_.split('_')[0]
                    label = labels[group][int(attr_.split('_')[1])]
                    attr['ALL'].update({attr_ : (group, label)})

            self._attr[subset] = attr

            print('Reading model scores for %s subset' % (subset))
            scores = {'ACCURACY' : dict(), 'PRECISION' : dict(), 'RECALL' : dict(), 'F1 SCORE' : dict()}
            for filter in FILTERS :
                scores['ACCURACY'][filter]  = list()
                scores['PRECISION'][filter] = list()
                scores['RECALL'][filter]    = list()
                scores['F1 SCORE'][filter]  = list()
                for model in MODELS :
                    name = f'%s_%s' % (subset, filter)
                    if filter == 'DALEX' :
                        name = f'%s_%s' % (name, model)

                    with open(f'%s/%s_%s.json' % (JSON_DIR, model, name), 'r') as f :
                        results = load_json(f)

                    scores['ACCURACY'][filter].append(results['ACCURACY'])
                    scores['PRECISION'][filter].append(results['PRECISION'])
                    scores['RECALL'][filter].append(results['RECALL'])
                    scores['F1 SCORE'][filter].append(results['F1 SCORE'])
            self._scores[subset] = scores

            print('Reading survey responses per question for %s subset' % (subset))
            df = ExcelIO().load_excel(f'%s_ALL' % subset)
            dists = dict()
            for column in self._attr[subset]['ALL'].keys() :
                counts = df.groupby(df[subset])[column].value_counts()
                answers = df[column].unique().tolist()
                dists[column] = {
                    'Normal'   : {answer : (counts['Normal'][answer]   if answer in counts['Normal']   else 0) for answer in answers},
                    'Possible' : {answer : (counts['Possible'][answer] if answer in counts['Possible'] else 0) for answer in answers}
                }
            self._dists[subset] = dists

            print('Reading cross-relations for %s subset' % (subset))
            bayes = dict()
            for target in SUBSETS :
                if target == subset :
                    continue

                bayes[target] = {'Normal' : dict(), 'Possible' : dict()}
                counts = self._labels.groupby(subset)[target].value_counts()
                A = counts['Normal']['Normal']
                B = counts['Normal']['Possible']
                C = counts['Possible']['Normal']
                D = counts['Possible']['Possible']

                bayes[target]['Normal']   = {'Normal' : round(((100 * A) / (A + C)), 2), 'Possible' : round((100 * C) / (A + C), 2)}
                bayes[target]['Possible'] = {'Normal' : round(((100 * B) / (B + D)), 2), 'Possible' : round((100 * D) / (B + D), 2)}
            self._bayes[subset] = bayes

    def get_selected_attributes(self, subset : str) -> dict :
        return self._attr[subset]

    def get_model_scores(self, subset : str) -> dict:
        return self._scores[subset]

    def get_response_distributions(self, subset) -> dict:
        return self._dists[subset]

    def get_cross_relations(self, subset) -> dict :
        return self._bayes[subset]
