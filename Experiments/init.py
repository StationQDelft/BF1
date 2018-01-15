### basics
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
config = cfg


### Namespace vars
class NameSpace:
    pass

namespace = NameSpace()


### Default Alazar settings
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
    trigger_level1=128+5,
    trigger_engine2='TRIG_ENGINE_K',
    trigger_source2='DISABLE',
    trigger_slope2='TRIG_SLOPE_POSITIVE',
    trigger_level2=128+5,
    external_trigger_coupling='DC',
    external_trigger_range='ETR_2V5',
    trigger_delay=0,
    timeout_ticks=0,
    aux_io_mode='AUX_IN_AUXILIARY',
    aux_io_param='NONE'
)

### Default AWG settings, in a language that AWG files speak
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


### Creating instruments
def init_instruments():
    from stationq.qctools import instruments as instools

    from qcodes.instrument_drivers.QuTech.IVVI import IVVI
    ivvi = instools.create_inst(IVVI, "ivvi", "ASRL5::INSTR")

    #from qcodes.instrument_drivers.stanford_research.SR865 import SR865
    #sr1 = instools.create_inst(SR865, "sr1", "GPIB0::3::INSTR")
    #
    #from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
    #key = instools.create_inst(Keysight_34465A, "key1", "USB0::0x2A8D::0x0101::MY57503596::INSTR")

    from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A
    RF = instools.create_inst(RohdeSchwarz_SGS100A, 'RF', address="TCPIP0::169.254.2.20")
    LO = instools.create_inst(RohdeSchwarz_SGS100A, 'LO', address="TCPIP0::169.254.234.107")

    from qcodes.instrument_drivers.AlazarTech.ATS9360 import AlazarTech_ATS9360
    alazar = instools.create_inst(AlazarTech_ATS9360, 'alazar')

    from qcodes.instrument_drivers.tektronix.AWG5014 import Tektronix_AWG5014
    awg = instools.create_inst(Tektronix_AWG5014, 'awg', address="TCPIP0::169.254.183.196::inst0::INSTR")

    from qcodes.instrument_drivers.rigol.DG4000 import Rigol_DG4000
    fg = instools.create_inst(Rigol_DG4000, 'fg', address="TCPIP0::169.254.190.44::inst0::INSTR")

    for i in range(1,16):
        ivvi.parameters['dac{}'.format(i)].set_step(0.5)
        ivvi.parameters['dac{}'.format(i)].set_delay(0.001)

    return qc.Station(ivvi, RF, LO, alazar, awg, fg)


###  Setting some reasonable initial values
def set_instrument_defaults(station):
    # IVVI
    ivvi = station.ivvi
    ivvi.dac1.set_delay(0.001)
    ivvi.dac1.set_step(20)
    ivvi.dac8.set_delay(0.001)
    ivvi.dac8.set_step(5)
    ivvi.dac12.set_delay(0.001)
    ivvi.dac12.set_step(5)
    ivvi.dac4.set_delay(0.001)
    ivvi.dac4.set_step(5)
    ivvi.dac5.set_delay(0.001)
    ivvi.dac5.set_step(5)
    ivvi.dac6.set_delay(0.001)
    ivvi.dac6.set_step(5)
    ivvi.dac7.set_delay(0.001)
    ivvi.dac7.set_step(5)

    # RF Sources
    station.RF.power(-55)
    station.RF.frequency(538.2e6)
    station.RF.on()
    station.LO.power(22)
    station.LO.frequency(station.RF.frequency()+20e6)
    station.LO.on()


if __name__ == '__main__':
    station = init_instruments()
    set_instrument_defaults(station)
