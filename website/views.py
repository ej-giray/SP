from flask                          import Blueprint, render_template, redirect, request, flash
from re                             import sub
from os                             import listdir
from subprocess                     import Popen

from website                        import DATA_DIR, JSON_DIR, XLSX_DIR
from website                        import SUBSETS, FILTERS, MODELS
from website.models                 import ResultsViewer, run_worker

views = Blueprint('views', __name__)

pipeline = Popen(['echo', ''], shell=True)
viewer   = ResultsViewer()

@views.route('/')
def home() :
    return redirect('/start')

@views.route('/start', methods=['GET'])
def start() :
    global pipeline
    if pipeline.poll() is None :
        pipeline.terminate()
        pipeline.wait()

    return render_template('start.html', error = False)

@views.route('/start', methods=['POST'])
def process() :
    if 'file' not in request.files:
        flash('No file part!')
        return render_template('start.html', error = True)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file!')
        return render_template('start.html', error = True)

    name = f'%s/%s' % (DATA_DIR, file.filename)
    file.save(name)

    global pipeline
    pipeline = run_worker(['pipeline', name])

    return ('', 204)

@views.route("/progress", methods=["GET"])
def track():
    current = (len(listdir(JSON_DIR)))
    total   = (len(SUBSETS) * 6 + len(SUBSETS) * len(FILTERS) * len(MODELS))
    progress = ((100 * current) / total)

    if progress == 100 and not viewer.is_loading():
        viewer.read_results()
        global pipeline
        if pipeline.poll() is None :
            pipeline.terminate()
            pipeline.wait()

    return str(progress)

@views.route('/results')
def results() :
    subset  = request.args.get('subset')
    subsets = SUBSETS
    scores  = viewer.get_model_scores(subset)
    metric_sub = {
        'ACCURACY'  : '(correctness of prediction)',
        'PRECISION' : '(effectivity against False Positives)',
        'RECALL'    : '(sensitivity against False Negatives)',
        'F1 SCORE'  : '(balance between Precision and Recall)'
    }
    metrics = dict()
    for metric, results in scores.items() :
        metrics[sub(' ', '_', metric)] = {
            'title'    : f'%s\\n%s' % (metric, metric_sub[metric]),
            'y_values' : f'[%s]' % (','.join([f'["%s", %s],' % (filter, ','.join([f'%.2f' % (item) for item in items])) for filter, items in results.items()]))
        }

    filter_alias  = {
        'CFS': 'CFS',
        'HNET': 'HNET',
        'DALEX_RFC': 'DALEX RF',
        'DALEX_CNB': 'DALEX NB',
        'DALEX_SVM': 'DALEX SVM',
        'DALEX_LRC': 'DALEX LR'
    }
    attributes    = viewer.get_selected_attributes(subset)
    distributions = viewer.get_response_distributions(subset)
    dists = dict()
    for column, groups in distributions.items() :
        dists[column] = {
            'Normal'   : f'[%s]' % (','.join([f'["%s", %i]' % (sub('"', '\\"', answer), count) for answer, count in groups['Normal'].items()])),
            'Possible' : f'[%s]' % (','.join([f'["%s", %i]' % (sub('"', '\\"', answer), count) for answer, count in groups['Possible'].items()]))
        }

    relations = viewer.get_cross_relations(subset)
    bayesian  = {
        'y_values' : f'[%s, %s]' % (
            f'["%s Normal", %s]' % (subset, ','.join([f'%.2f' % (item['Normal']) for items in relations.values() for item in items.values()])),
            f'["%s %s", %s]' % (subset, ('Possible' if subset != 'SLEEP' else 'Poor'), ','.join([f'%.2f' % (item['Possible']) for items in relations.values() for item in items.values()]))
        ),
        'x_values' : f'[%s]' % (','.join([f'"%s\\n%s"' % (target, (label if target != 'SLEEP' or label == 'Normal' else 'Poor')) for target, labels in relations.items() for label in labels])),
        'groups'   : f'[["%s Normal", "%s %s"]]' % (subset, subset, ('Possible' if subset != 'SLEEP' else 'Poor'))
    }

    return render_template('results.html', **locals())
