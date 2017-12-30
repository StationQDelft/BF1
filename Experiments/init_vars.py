import logging

logger = logging.getLogger('measurement')
logger.setLevel(logging.INFO)

h = logging.StreamHandler()
h.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')
h.setFormatter(fmt)
logger.handlers = [h]
logger.info('Logger set up!')


from IPython import get_ipython
ipython = get_ipython()

import qcodes
qc = qcodes

import labpythonconfig as cfg


# Namespace vars
class NameSpace:
    pass

namespace = NameSpace()


# Default Alazar settings
namespace.ats_settings = dict(
    clock_source='INTERNAL_CLOCK',
    sample_rate=int(1e9),
    clock_edge='CLOCK_EDGE_RISING',
    decimation=1,
    coupling=['DC','DC'],
    channel_range=[.4, .4],
    impedance=[50, 50],
    trigger_operation='TRIG_ENGINE_OP_J',
    trigger_engine1='TRIG_ENGINE_J',
    trigger_source1='CHANNEL_A',
    trigger_slope1='TRIG_SLOPE_POSITIVE',
    trigger_level1=128+3,
    trigger_engine2='TRIG_ENGINE_K',
    trigger_source2='DISABLE',
    trigger_slope2='TRIG_SLOPE_POSITIVE',
    trigger_level2=128,
    external_trigger_coupling='DC',
    external_trigger_range='ETR_2V5',
    trigger_delay=0,
    timeout_ticks=0,
    aux_io_mode='AUX_IN_AUXILIARY',
    aux_io_param='NONE'
)

# Default AWG settings, in a language that AWG files speak
namespace.awg_settings = {
    'sampling_rate' : int(1e9),
    'clock_source' : 1,
    'reference_source' : 2,
    'external_reference_type' : 1,
    'trigger_source' : 1,
    'trigger_input_impedance' : 1,
    'trigger_input_threshold' : 0.5,
    'run_mode' : 4,
    'run_state' : 0,
}

for i in range(1,5):
    namespace.awg_settings[f'channel_{i}'] = {
        'channel_state' : 2,
        'analog_amplitude' : 2.0,
        'analog_offset' : 0.0,
    }
