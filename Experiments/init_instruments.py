from stationq.qctools import instruments as instools

from qcodes.instrument_drivers.QuTech.IVVI import IVVI
ivvi = instools.create_inst(IVVI, "ivvi", "ASRL5::INSTR")

from qcodes.instrument_drivers.stanford_research.SR865 import SR865
# sr1 = instools.create_inst(SR865, "sr1", "GPIB0::3::INSTR")

from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
key = instools.create_inst(Keysight_34465A, "key1", "USB0::0x2A8D::0x0101::MY57503596::INSTR")

from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A
RF = instools.create_inst(RohdeSchwarz_SGS100A, 'RF', address="TCPIP0::169.254.2.20")
LO = instools.create_inst(RohdeSchwarz_SGS100A, 'LO', address="TCPIP0::169.254.234.107")

from qcodes.instrument_drivers.AlazarTech.ATS9360 import AlazarTech_ATS9360
alazar = instools.create_inst(AlazarTech_ATS9360, 'alazar')

from qcodes.instrument_drivers.rigol.DG4000 import Rigol_DG4000
fg = instools.create_inst(Rigol_DG4000, 'fg', address="TCPIP0::169.254.190.44::inst0::INSTR")

for i in range(1,16):
    ivvi.parameters['dac{}'.format(i)].set_step(0.5)
    ivvi.parameters['dac{}'.format(i)].set_delay(0.001)
