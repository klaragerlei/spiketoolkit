from spikeextractors import RecordingExtractor
import numpy as np

class ScaleTracesRecording(RecordingExtractor):
    def __init__(self, recording, scalar):
        '''
        Scales the traces from the given recording extractor
        Parameters
        ----------
        recording: RecordingExtractor
            The recording extractor to be scaled
        scalar: int or float
            Scalar for the traces of the recording extractor
        '''
        RecordingExtractor.__init__(self)
        if not isinstance(recording, RecordingExtractor):
            raise ValueError("'recording' must be a RecordingExtractor")
        self._recording = recording
        self._scalar = scalar
        self.copy_channel_properties(recording=self._recording)

    def get_sampling_frequency(self):
        return self._recording.get_sampling_frequency()

    def get_num_frames(self):
        return self._recording.get_num_frames()

    def get_channel_ids(self):
        return self._recording.get_channel_ids()

    def get_traces(self, channel_ids=None, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self.get_num_frames()
        if channel_ids is None:
            channel_ids = self.get_channel_ids()
        traces = self._recording.get_traces(channel_ids=channel_ids, start_frame=start_frame, end_frame=end_frame)*self._scalar
        return traces


def scale_traces(recording, scalar):
    return ScaleTracesRecording(
        recording=recording, scalar=scalar
    )