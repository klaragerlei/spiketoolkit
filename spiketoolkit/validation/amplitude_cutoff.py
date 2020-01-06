from .quality_metric import QualityMetric
import numpy as np
import spikemetrics.metrics as metrics
from spiketoolkit.curation.thresholdcurator import ThresholdCurator

class AmplitudeCutoff(QualityMetric):
    def __init__(
        self,
        metric_data,
    ):
        QualityMetric.__init__(self, metric_data)
        if not metric_data.has_amplitudes():
            raise ValueError("MetricData object must have amplitudes")

    def compute_metric(self):
        amplitude_cutoffs_epochs = []
        for epoch in self._metric_data._epochs:
            in_epoch = np.logical_and(
                self._metric_data._spike_times_amps > epoch[1], self._metric_data._spike_times_amps < epoch[2]
            )
            amplitude_cutoffs_all = metrics.calculate_amplitude_cutoff(
                self._metric_data._spike_clusters_amps[in_epoch],
                self._metric_data._amplitudes[in_epoch],
                self._metric_data._total_units,
                verbose=self._metric_data.verbose,
            )
            amplitude_cutoffs_list = []
            for i in self._metric_data._unit_indices:
                amplitude_cutoffs_list.append(amplitude_cutoffs_all[i])
            amplitude_cutoffs = np.asarray(amplitude_cutoffs_list)
            amplitude_cutoffs_epochs.append(amplitude_cutoffs)
        return amplitude_cutoffs_epochs

    def threshold_metric(self, threshold, threshold_sign, epoch=0):
        assert (epoch < len(self._metric_data.get_epochs())), "Invalid epoch specified"
        amplitude_cutoff_epochs = self.compute_metric()[epoch]
        tc = ThresholdCurator(sorting=self._metric_data._sorting, metrics_epoch=amplitude_cutoff_epochs)
        tc.threshold_sorting(threshold=threshold, threshold_sign=threshold_sign)
        return tc
