from sfl_diagnoser.Diagnoser import Barinel

class FullMatrix(object):
    def __init__(self):
        self.matrix=[] # matrix size define the num of tests
        self.probabilities=[] # probabilities size define the num of components
        self.error=[]

    def diagnose(self):
        bar= Barinel.Barinel()
        bar.set_matrix_error(self.matrix,self.error)
        bar.set_prior_probs(self.probabilities)
        return bar.run()

    def save_to_csv_file(self, out_file):
        import csv
        lines = [self.probabilities] + map(lambda x : x[0] + [x[1]] ,zip(self.matrix, self.error))
        with open(out_file, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(lines)

    # optimization: remove unreachable components & components that pass all their tests
    # return: optimized FullMatrix, chosen_components( indices)
    @staticmethod
    def optimize_FullMatrix(fullMatrix):
        chosen=[]
        UnusedComps=range(len(fullMatrix.probabilities))
        for test,err in zip(fullMatrix.matrix,fullMatrix.error):
            if err==0:
                continue
            for comp in list(UnusedComps):
                if test[comp]==1:
                    chosen.append(comp)
                    UnusedComps.remove(comp)
        optimizedMatrix=FullMatrix()
        optimizedMatrix.probabilities=[x[1] for x in enumerate(fullMatrix.probabilities) if x[0] in chosen]
        newErr=[]
        newMatrix=[]
        for test,err in zip(fullMatrix.matrix,fullMatrix.error):
            newTest=[x[1] for x in enumerate(test) if x[0] in chosen]
            if 1 in newTest: ## optimization could remove all comps of a test
                newMatrix.append(newTest)
                newErr.append(err)
        optimizedMatrix.matrix=newMatrix
        optimizedMatrix.error=newErr
        return optimizedMatrix,sorted(chosen)