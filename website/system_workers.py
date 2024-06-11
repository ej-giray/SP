from pandas                         import DataFrame, get_dummies, crosstab, concat
from math                           import sqrt, log, fabs
from os                             import path
from json                           import dump as dump_json
from pickle                         import dump as dump_bin
from pickle                         import load as load_bin
from numpy                          import trace, sum

from dalex                          import Explainer
from sklearn.ensemble               import RandomForestClassifier
from sklearn.naive_bayes            import ComplementNB
from sklearn.svm                    import LinearSVC
from sklearn.linear_model           import LogisticRegression
from sklearn.model_selection        import train_test_split
from sklearn.metrics                import confusion_matrix, precision_recall_fscore_support

from website                        import BINS_DIR, JSON_DIR
from website.excel_io               import ExcelIO

INVALID = -999.0

classifiers = {
    'RFC' : RandomForestClassifier(random_state=0, class_weight='balanced'),
    'CNB' : ComplementNB(),
    'SVM' : LinearSVC(random_state=0, class_weight='balanced', max_iter=5000),
    'LRC' : LogisticRegression(random_state=0, class_weight='balanced', max_iter=5000)
}

class CFS :
    # code adapted from CfsSubsetEval.java in WEKA
    def __init__(self, subset : str) :
        self._subset = subset
        self._df     = ExcelIO().load_excel(f'%s_ALL' % (self._subset))
        print(f'Initializing CFS selector on %s subset' % (self._subset))

        columns = self._df.columns.tolist()
        size    = len(columns)
        self.corr = {columns[i] : {columns[j] : INVALID for j in range(i + 1, size)} for i in range(size - 1)}

    def entropyd(self, val : float) -> float:
        return (0.0 if val < 1e-6 else val * log(val))

    def su_corr(self, att1 : DataFrame, att2 : DataFrame) -> float:
        xtab = crosstab(att1, att2)
        ent_col = 0
        total   = 0
        for col in xtab.sum(axis=1) :
            ent_col += self.entropyd(col)
            total   += col
        ent_col -= self.entropyd(total)

        ent_row = 0
        for row in xtab.sum(axis=0) :
            ent_row += self.entropyd(row)

        ent_cond = 0
        for row in xtab.index.tolist() :
            for col in xtab.columns.tolist() :
                ent_cond += self.entropyd(xtab.at[row, col])
        ent_cond -= ent_row
        ent_row -= self.entropyd(total)

        return (2 * (ent_col - ent_cond)) / (ent_col + ent_row)

    def evaluate_subset(self, subset : DataFrame) -> float :
        target = subset.columns[-1]
        source = subset.columns.tolist()
        source.remove(target)
        size = len(source)

        rcf = 0
        for att1 in source :
            if self._df.columns.get_loc(att1) > self._df.columns.get_loc(target) :
                att1, target = target, att1
            if self.corr[att1][target] == INVALID :
                self.corr[att1][target] = self.su_corr(subset[att1], subset[target])
            rcf += self.corr[att1][target]

        if rcf == 0 :
            return 0.00

        rff = 0
        for i in range(0, size - 1) :
            for j in range(i + 1, size) :
                att1, att2 = source[i], source[j]
                if self._df.columns.get_loc(att1) > self._df.columns.get_loc(att2) :
                    att1, att2 = source[j], source[i]

                if self.corr[att1][att2] == INVALID :
                    self.corr[att1][att2] = self.su_corr(subset[att1], subset[att2])
                rff += self.corr[att1][att2]

        return fabs(rcf) / sqrt(size + 2 * fabs(rff))

    def run_selection(self) -> None :
        print(f'Running CFS selection on %s subset' % (self._subset))
        target = self._df.columns[-1]
        source = self._df.columns.tolist()
        source.remove(target)

        best_global   = 0
        select_global = dict()
        while True :
            selected   = None
            best_local = best_global
            for attr in source :
                merit = self.evaluate_subset(self._df[list(select_global.keys()) + [attr] + [target]])
                if merit > best_local :
                    best_local = merit
                    selected   = attr

            if selected != None :
                select_global.update({selected : (best_local - best_global)})
                best_global = best_local
                source.remove(selected)
            else :
                break

        # update locally predictive values as long as no existing feature has
        # a higher merit than the new ones
        while True :
            best_local = 0
            selected   = None
            for attr in source :
                merit = self.evaluate_subset(self._df[[attr] + [target]])
                if merit > best_local :
                    best_local = merit
                    selected = attr

            if best_local == 0 :
                break

            source.remove(selected)
            ok = True
            for attr in select_global.keys() :
                merit = self.evaluate_subset(self._df[[attr] + [selected]])
                if merit > best_local :
                    ok = False
                    break

            if ok :
                select_global.update({selected : (best_local - best_global)})

        # update feature importance
        baseline = list(select_global.values())[-1]
        for attr, values in select_global.items() :
            select_global.update({attr : round((values + fabs(baseline) + 0.01), 2)})

        headers = [header for header in list(self._df) if header in select_global.keys()]
        self._df = self._df[headers + [self._subset]]

        with open(f'%s/AFS_%s_CFS.json' % (JSON_DIR, self._subset), 'w') as f :
            dump_json(select_global, f, indent=4)

        ExcelIO().save_excel('%s_CFS' % (self._subset), self._df)

class HNET :
    def __init__(self, subset : str) :
        self._subset = subset
        self._df     = ExcelIO().load_excel(f'%s_ALL' % (self._subset))
        print(f'Initializing HNET selector on %s subset' % (self._subset))

        bin = f'%s/%s_HNET.bin' % (BINS_DIR, subset)
        if not path.exists(bin) :
            from hnet import hnet
            hnet = hnet()
            results = hnet.association_learning(self._df)

            with open(bin, 'wb') as f:
                dump_bin(results, f)
        else :
            with open(bin, 'rb') as f:
                results = load_bin(f)
        self._logp = results['simmatLogP']

    def run_selection(self) -> None :
        print(f'Running HNET selection on %s subset' % (self._subset))
        scores = concat([self._logp[f'%s_Normal' % (self._subset)], self._logp[f'%s_Possible' % (self._subset)]], axis=0)

        features = dict()
        for attr, value in scores.loc[scores > 0].sort_values(ascending=False).items() :
            attr = f'%s_%s' % (attr.split('_')[0], attr.split('_')[1])
            if attr not in features.keys() :
                features[attr] = round(value, 2)

        headers  = [header for header in list(self._df) if header in features.keys()]
        self._df = self._df[headers + [self._subset]]

        with open(f'%s/AFS_%s_HNET.json' % (JSON_DIR, self._subset), 'w') as f :
            dump_json(features, f, indent=4)

        ExcelIO().save_excel('%s_HNET' % (self._subset), self._df)

class DALEX :
    def __init__(self, model : str, subset : str) :
        self._model  = model
        self._subset = subset
        self._df     = ExcelIO().load_excel(f'%s_ALL' % (self._subset))
        print(f'Initializing DALEX %s selector on %s subset' % (self._model, self._subset))

        bin = f'%s/%s_DALEX_%s.bin' % (BINS_DIR, self._subset, self._model)
        if not path.exists(bin) :
            x = get_dummies(self._df[self._df.columns[:-1]].copy())
            y = self._df[self._df.columns[-1]].copy().map({'Normal': 0, 'Possible': 1}).astype(int)
            x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0)

            classifier = classifiers[self._model]
            classifier.fit(x_train, y_train)

            exp = Explainer(classifier, x_test, y_test)
            obj = exp.model_parts(loss_function='rmse', random_state=0)
            with open(bin, 'wb') as f :
                dump_bin(obj, f)
        else :
            with open(bin, 'rb') as f :
                obj = load_bin(f)

        self._vi = obj.result

    def run_selection(self) -> None :
        print(f'Running DALEX %s selection on %s subset' % (self._model, self._subset))
        vi = self._vi
        fm = vi[vi.variable == '_full_model_'].dropout_loss.values[0]
        vi = vi.loc[(vi['dropout_loss'] - fm) >= 0.0001]
        vi = vi.sort_values('dropout_loss', ascending=False)

        features = dict()
        for idx, row in vi.iterrows() :
            if row['variable'] in ['_baseline_', '_full_model_'] :
                continue

            attr = f'%s_%s' % (row['variable'].split('_')[0], row['variable'].split('_')[1])
            if attr not in features.keys() :
                features[attr] = round((row['dropout_loss'] - fm) * 100, 2)

        headers  = [header for header in list(self._df) if header in features.keys()]
        self._df = self._df[headers + [self._subset]]

        with open(f'%s/AFS_%s_DALEX_%s.json' % (JSON_DIR, self._subset, self._model), 'w') as f :
            dump_json(features, f, indent=4)

        ExcelIO().save_excel('%s_DALEX_%s' % (self._subset, self._model), self._df)

class ModelEvaluator :
    def __init__(self, model : str, subset : str) :
        self._model  = model
        self._subset = subset
        print(f'Initializing %s evaluator on %s subset' % (self._model, self._subset))

        self._data = ExcelIO().load_excel(f'%s' % (self._subset))

    def __del__(self) :
        pass

    def train_and_evaluate(self) -> None :
        print(f'Running evaluation of %s on 70-train, 30-test split %s subset' % (self._model, self._subset))
        classifier = classifiers[self._model]
        x = get_dummies(self._data[self._data.columns[:-1]].copy())
        y = self._data[self._data.columns[-1]].copy().map({'Normal': 0, 'Possible': 1}).astype(int)
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=0)

        classifier.fit(x_train, y_train)
        y_pred = classifier.predict(x_test)
        matrix = confusion_matrix(y_test, y_pred)
        report = precision_recall_fscore_support(y_test, y_pred, average='weighted')

        results = {
            'ACCURACY'  : round((100 * trace(matrix) / sum(matrix)), 2),
            'PRECISION' : round((100 * report[0]), 2),
            'RECALL'    : round((100 * report[1]), 2),
            'F1 SCORE'  : round((100 * report[2]), 2)
        }

        with open(f'%s/%s_%s.json' % (JSON_DIR, self._model, self._subset), 'w') as f :
            dump_json(results, f, indent=4)
