from sys                            import argv

from website.models                 import PipelineRunner
from website.system_workers         import CFS, HNET, DALEX, ModelEvaluator

if __name__ == '__main__' :
    process = argv[1]
    subset  = argv[2]
    if len(argv) > 3 :
        model = argv[3]

    if process == "pipeline"  :
        model = PipelineRunner(subset)
        model.run_attribute_selectors()
        model.run_model_evaluators()
    elif process == 'CFS' :
        CFS(subset).run_selection()
    elif process == 'HNET' :
        HNET(subset).run_selection()
    elif process == 'DALEX' :
        DALEX(model, subset).run_selection()
    elif process == 'EVALUATE':
        ModelEvaluator(model, subset).train_and_evaluate()
    else :
        print('Unknown process to spawn.')
