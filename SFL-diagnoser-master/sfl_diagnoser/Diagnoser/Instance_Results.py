
class Instance_Results(object):
    def __init__(self, experiment_instance):
        self.instance = experiment_instance
        self.metrics = self._calculate_metrics(experiment_instance)
        for key, value in self.metrics:
            setattr(self, key, value)

    def _calculate_metrics(self, experiment_instance):
        """
        calc result for the given experiment instance
        :param experiment_instance:
        :return: dictionary of (metric_name, metric value)
        """
        metrics = {}

        return metrics

    def _get_metrics_list(self):
        return sorted(self.metrics.items(), key=lambda m:m[0])

    def get_metrics_values(self):
        return map(lambda m:m[1], self._get_metrics_list())

    def get_metrics_names(self):
        return map(lambda m:m[0], self._get_metrics_list())
