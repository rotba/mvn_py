from sfl_diagnoser.Diagnoser.Experiment_Data import Experiment_Data
from sfl_diagnoser.Diagnoser.Ochiai_Rank import Ochiai_Rank
from scipy.stats import entropy

class Diagnosis_Results(object):
    def __init__(self, diagnoses, initial_tests, error, pool=None, bugs=None):
        self.diagnoses = diagnoses
        self.initial_tests = initial_tests
        self.error = error
        self.pool = pool
        if pool == None:
            self.pool = Experiment_Data().POOL
        self.bugs = bugs
        if bugs == None:
            self.bugs = Experiment_Data().BUGS
        self.components = set(reduce(list.__add__ , map(lambda test: test[1], filter(lambda test: test[0] in self.initial_tests, self.pool.items())), []))
        self.metrics = self._calculate_metrics()
        for key, value in self.metrics.items():
            setattr(self, key, value)

    def _calculate_metrics(self):
        """
        calc result for the given experiment instance
        :param experiment_instance:
        :return: dictionary of (metric_name, metric value)
        """
        metrics = {}
        precision, recall = self.calc_precision_recall()
        metrics["precision"] = precision
        metrics["recall"] = recall
        metrics["entropy"] = self.calc_entropy()
        metrics["component_entropy"] = self.calc_component_entropy()
        metrics["num_comps"] = len(self.get_components())
        metrics["num_tests"] = len(self.get_tests())
        metrics["num_distinct_traces"] = len(self.get_distinct_traces())
        metrics["num_failed_tests"] = len(self._get_tests_by_error(1))
        passed_comps = set(self._get_components_by_error(0))
        failed_comps = set(self.get_components_in_failed_tests())
        metrics["num_failed_comps"] = len(failed_comps)
        metrics["only_failed_comps"] = len(failed_comps - passed_comps)
        metrics["only_passed_comps"] = len(passed_comps - failed_comps)
        metrics["num_bugs"] = len(self.get_bugs())
        metrics["wasted"] = self.calc_wasted_components()
        metrics["top_k"] = self.calc_top_k()
        metrics["ochiai"] = self.calc_ochiai_values()
        return metrics

    def _get_metrics_list(self):
        return sorted(self.metrics.items(), key=lambda m:m[0])

    def get_metrics_values(self):
        return map(lambda m:m[1], self._get_metrics_list())

    def get_metrics_names(self):
        return map(lambda m:m[0], self._get_metrics_list())

    def __repr__(self):
        return repr(self.metrics)

    @staticmethod
    def precision_recall_for_diagnosis(buggedComps, dg, pr, validComps):
        fp = len([i1 for i1 in dg if i1 in validComps])
        fn = len([i1 for i1 in buggedComps if i1 not in dg])
        tp = len([i1 for i1 in dg if i1 in buggedComps])
        tn = len([i1 for i1 in validComps if i1 not in dg])
        if ((tp + fp) == 0):
            precision = "undef"
        else:
            precision = (tp + 0.0) / float(tp + fp)
            a = precision
            precision = precision * float(pr)
        if ((tp + fn) == 0):
            recall = "undef"
        else:
            recall = (tp + 0.0) / float(tp + fn)
            recall = recall * float(pr)
        return precision, recall

    def calc_precision_recall(self):
        recall_accum=0
        precision_accum=0
        validComps=[x for x in set(reduce(list.__add__, self.pool.values())) if x not in self.get_bugs()]
        for d in self.diagnoses:
            dg=d.diagnosis
            pr=d.probability
            precision, recall = Diagnosis_Results.precision_recall_for_diagnosis(self.get_bugs(), dg, pr, validComps)
            if(recall!="undef"):
                recall_accum=recall_accum+recall
            if(precision!="undef"):
                precision_accum=precision_accum+precision
        return precision_accum,recall_accum

    def get_tests(self):
        return self.pool.items()

    def get_bugs(self):
        return self.bugs

    def get_initial_tests_traces(self):
        return map(lambda test: (sorted(test[1]), self.error[test[0]]),
            filter(lambda test: test[0] in self.initial_tests, self.pool.items()))

    def _get_tests_by_error(self, error):
        tests = filter(lambda test: test[0] in self.initial_tests, self.pool.items())
        return dict(filter(lambda test: self.error[test[0]] == error, tests))

    def get_components(self):
        return set(reduce(list.__add__, self.pool.values()))

    def _get_components_by_error(self, error):
        return set(reduce(list.__add__, self._get_tests_by_error(error).values(), []))

    def get_components_in_failed_tests(self):
        return self._get_components_by_error(1)

    def get_components_in_passed_tests(self):
        return self._get_components_by_error(0)

    def get_components_probabilities(self):
        """
        calculate for each component c the sum of probabilities of the diagnoses that include c
        return dict of (component, probability)
        """
        compsProbs={}
        for d in self.diagnoses:
            p = d.get_prob()
            for comp in d.get_diag():
                compsProbs[comp] = compsProbs.get(comp,0) + p
        return sorted(compsProbs.items(), key=lambda x: x[1], reverse=True)

    def calc_wasted_components(self):
        if len(self.get_bugs()) == 0:
            return float('inf')
        components = map(lambda x: x[0], self.get_components_probabilities())
        wasted = 0.0
        for b in self.get_bugs():
            if b not in components:
                return float('inf')
            wasted += components.index(b)
        return wasted / len(self.get_bugs())

    def calc_top_k(self):
        components = map(lambda x: x[0], self.get_components_probabilities())
        top_k = float('inf')
        for bug in self.get_bugs():
            if bug in components:
                top_k = min(top_k, components.index(bug))
        return top_k + 1

    def calc_entropy(self):
        return entropy(map(lambda diag: diag.probability, self.diagnoses))

    def calc_component_entropy(self):
        return entropy(map(lambda x: x[1], self.get_components_probabilities()))

    def get_uniform_entropy(self):
        uniform_probability = 1.0/len(self.diagnoses)
        return entropy(map(lambda diag: uniform_probability, self.diagnoses))

    def get_distinct_traces(self):
        distinct_tests = set(map(str, self.get_initial_tests_traces()))
        return distinct_tests

    def calc_ochiai_values(self):
        ochiai = {}
        for component in self.components:
            ochiai[component] = Ochiai_Rank()
        for trace, error in self.get_initial_tests_traces():
            for component in self.components:
                    ochiai[component].advance_counter(1 if component in trace else 0, error)
        return ochiai

