import spikeextractors as se

import os
from os.path import join
from ..tools import _run_command_and_print_output, _spikeSortByProperty
import time


def ironclust(recording,  # Recording object
              prm_template_name=None,  # Name of the template file
              by_property=None,
              output_folder=None,  # Temporary working directory
              detect_sign=-1,  # Polarity of the spikes, -1, 0, or 1
              adjacency_radius=-1,  # Channel neighborhood adjacency radius corresponding to geom file
              detect_threshold=5,  # Threshold for detection
              merge_thresh=.98,  # Cluster merging threhold 0..1
              freq_min=300,  # Lower frequency limit for band-pass filter
              freq_max=6000,  # Upper frequency limit for band-pass filter
              pc_per_chan=3,  # Number of pc per channel
              ironclust_path=None
):
    t_start_proc = time.time()
    if by_property is None:
        sorting = _ironclust(recording, prm_template_name, output_folder, detect_sign, adjacency_radius,
                             detect_threshold, merge_thresh, freq_min, freq_max, pc_per_chan, ironclust_path)
    else:
        if by_property in recording.getChannelPropertyNames():
            sorting = _spikeSortByProperty(recording, 'ironclust', by_property, prm_template_name=prm_template_name,
                                           output_folder=output_folder, detect_sign=detect_sign,
                                           adjacency_radius=adjacency_radius, detect_threshold=detect_threshold,
                                           merge_thresh=merge_thresh, freq_min=freq_min, freq_max=freq_max,
                                           pc_per_chan=pc_per_chan, ironclust_path=ironclust_path)
        else:
            print("Property not available! Running normal spike sorting")
            sorting = _ironclust(recording, prm_template_name, output_folder, detect_sign, adjacency_radius,
                                 detect_threshold, merge_thresh, freq_min, freq_max, pc_per_chan, ironclust_path)

    print('Elapsed time: ', time.time() - t_start_proc)

    return sorting


def _ironclust(recording,  # Recording object
               prm_template_name,  # Name of the template file
               output_folder=None,  # Temporary working directory
               detect_sign=-1,  # Polarity of the spikes, -1, 0, or 1
               adjacency_radius=-1,  # Channel neighborhood adjacency radius corresponding to geom file
               detect_threshold=5,  # Threshold for detection
               merge_thresh=.98,  # Cluster merging threhold 0..1
               freq_min=300,  # Lower frequency limit for band-pass filter
               freq_max=6000,  # Upper frequency limit for band-pass filter
               pc_per_chan=3,  # Number of pc per channel
               ironclust_path=None
               ):
    try:
        from mountainlab_pytools import mdaio
    except ModuleNotFoundError:
        raise ModuleNotFoundError("\nTo use IronClust, install mountainlab_pytools: \n\n"
                                  "\npip install mountainlab_pytools\n"
                                  "and clone the repo:\n"
                                  "git clone https://github.com/jamesjun/ironclust")
    if ironclust_path is None:
        ironclust_path = os.getenv('IRONCLUST_PATH', None)
    if not ironclust_path:
        raise Exception(
            'You must either set the IRONCLUST_PATH environment variable, or pass the ironclust_path parameter')
    if not os.path.isfile(join(ironclust_path, 'p_ironclust.m')):
        raise ModuleNotFoundError("\nTo use IronClust clone the repo:\n\n"
                                  "git clone https://github.com/jamesjun/ironclust")
    source_dir = os.path.dirname(os.path.realpath(__file__))

    if output_folder is None:
        dataset_dir = './ironclust_dataset'
        output_folder = '.'
    else:
        dataset_dir = join(output_folder, 'ironclust_dataset')
        if not os.path.isdir(dataset_dir):
            os.makedirs(dataset_dir)
    dataset_dir = os.path.abspath(dataset_dir)
    output_folder = os.path.abspath(output_folder)

    # Generate three files in the dataset directory: raw.mda, geom.csv, params.json
    se.MdaRecordingExtractor.writeRecording(recording=recording, save_path=dataset_dir)

    samplerate = recording.getSamplingFrequency()

    print('Reading timeseries header...')
    HH = mdaio.readmda_header(dataset_dir + '/raw.mda')
    num_channels = HH.dims[0]
    num_timepoints = HH.dims[1]
    duration_minutes = num_timepoints / samplerate / 60
    print('Num. channels = {}, Num. timepoints = {}, duration = {} minutes'.format(num_channels, num_timepoints,
                                                                                   duration_minutes))

    print('Creating .params file...')
    txt = ''
    txt += 'samplerate={}\n'.format(samplerate)
    txt += 'detect_sign={}\n'.format(detect_sign)
    txt += 'adjacency_radius={}\n'.format(adjacency_radius)
    txt += 'detect_threshold={}\n'.format(detect_threshold)
    txt += 'merge_thresh={}\n'.format(merge_thresh)
    txt += 'freq_min={}\n'.format(freq_min)
    txt += 'freq_max={}\n'.format(freq_max)
    txt += 'pc_per_chan={}\n'.format(pc_per_chan)
    txt += 'prm_template_name={}\n'.format(prm_template_name)
    _write_text_file(dataset_dir + '/argfile.txt', txt)

    print('Running IronClust...')
    cmd_path = "addpath('{}', '{}/matlab', '{}/mdaio');".format(ironclust_path, ironclust_path, ironclust_path)
    # "p_ironclust('$(tempdir)','$timeseries$','$geom$','$prm$','$firings_true$','$firings_out$','$(argfile)');"
    cmd_call = "p_ironclust('{}', '{}', '{}', '', '', '{}', '{}');" \
        .format(output_folder, dataset_dir + '/raw.mda', dataset_dir + '/geom.csv', output_folder + '/firings.mda',
                dataset_dir + '/argfile.txt')
    cmd = 'matlab -nosplash -nodisplay -r "{} {} quit;"'.format(cmd_path, cmd_call)
    print(cmd)
    retcode = _run_command_and_print_output(cmd)

    if retcode != 0:
        raise Exception('IronClust returned a non-zero exit code')

    # parse output
    result_fname = output_folder + '/firings.mda'
    if not os.path.exists(result_fname):
        raise Exception('Result file does not exist: ' + result_fname)

    firings = mdaio.readmda(result_fname)
    sorting = se.NumpySortingExtractor()
    sorting.setTimesLabels(firings[1, :], firings[2, :])
    return sorting


def _read_text_file(fname):
    with open(fname) as f:
        return f.read()


def _write_text_file(fname, str):
    with open(fname, 'w') as f:
        f.write(str)
