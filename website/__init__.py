REUSE_DATA = False

DATA_DIR = 'website/data'
BINS_DIR = f'%s/bins' % (DATA_DIR)
JSON_DIR = f'%s/json' % (DATA_DIR)
XLSX_DIR = f'%s/xlsx' % (DATA_DIR)

SUBSETS = ['DEPRESSION', 'ANXIETY', 'STRESS', 'SLEEP']
FILTERS = ['ALL', 'CFS', 'HNET', 'DALEX']
MODELS  = ['RFC', 'CNB', 'SVM', 'LRC']

SECTIONS = {
    'DEMOGRAPHICS' : (  0,  60),
    'LIFESTYLE'    : ( 60, 155),
    'PSQI'         : (155, 215),
    'DASS-21'      : (215, 236),
    'BRIEF-COPE'   : (236, 264)
}
