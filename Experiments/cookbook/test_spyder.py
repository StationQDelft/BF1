# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import time
import numpy as np
import matplotlib as mpl

from importlib import reload
from matplotlib import pyplot as plt

from labtools import mplplots; reload(mplplots)
from labtools.mplplots import tools as mpltools

import qcodes as qc
from qcodes.dataset.measurements import Measurement
from qcodes.dataset.plotting import plot_by_id

from pytopo.qctools import instruments as instools

from qcodes.instrument_drivers.QuTech.IVVI import IVVI
ivvi = instools.create_inst(IVVI, "ivvi", "ASRL5::INSTR")

from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
key1 = instools.create_inst(Keysight_34465A, "key1", "USB0::0x2A8D::0x0101::MY57503556::INSTR")
key2 = instools.create_inst(Keysight_34465A, "key2", "USB0::0x2A8D::0x0101::MY57503135::INSTR")

station = qc.Station(ivvi, key1, key2)

meas = Measurement()
meas.register_parameter(ivvi.dac1)
meas.register_parameter(key1.volt, setpoints=(ivvi.dac1, ))
meas.register_parameter(key2.volt, setpoints=(ivvi.dac1, ))

fig, ax = plt.subplots(1,1)

with meas.run() as datasaver:
    for bias_v in np.linspace(-100, 100, 11):
        ivvi.dac1(bias_v)
        current = key1.volt()
        voltage = key2.volt()
        
        datasaver.add_result((ivvi.dac1, bias_v), (key1.volt, current), (key2.volt, voltage))
        
        bias_vals = datasaver.dataset.get_data('ivvi_dac1')
        cur_vals = datasaver.dataset.get_data('key1_volt')
        volt_vals = datasaver.dataset.get_data('key2_volt')

        ax.clear()
        ax.plot(bias_vals, cur_vals, 'ko')
        ax.plot(bias_vals, volt_vals, 'ro')
        mpltools.process_events(fig)
        
        time.sleep(0.01)
        
mpltools.process_events(fig)
mpltools.update_and_copy(fig)