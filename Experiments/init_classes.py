import time
from collections import OrderedDict
import numpy as np

from qcodes.instrument_drivers.AlazarTech.acq_controllers import ATS9360Controller

from stationq.qctools import instruments as instools
from stationq.data.data_storage import Data, GridData
from stationq.experiment.measurement import Parameter, BaseMeasurement, PysweepGrid
from stationq.experiment.ATS import AlazarMeasurement


class TrigController(ATS9360Controller):
    fg = None

    def pre_acquire(self):
        time.sleep(1e-3)
        self.fg.ch1_output_enabled(True)

    def post_acquire(self):
        self.fg.ch1_output_enabled(False)
        time.sleep(5e-3)
        return super().post_acquire()


class Reflectometry(AlazarMeasurement):

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        self.ats_demod(True)
        self.ats_integrate_samples(True)


    def setup(self):
        super().setup()
        self.IF(abs(self.station.RF.frequency() - self.station.LO.frequency()))
        self.setup_alazar()


    def alazar_axes(self, shape):
        ret = OrderedDict({})
        for i, s in enumerate(shape):
            ret["Axis {}".format(i)] = {'value' : np.arange(s), 'independent_parameter' : True}

        return ret


    def measure_datapoint(self, station, namespace):
        A, B = self.acquire()
        phiA = np.angle(A, deg=True)
        if type(phiA) == np.ndarray:
            phiA[phiA < 0] += 360.
        phiB = np.angle(B, deg=True)
        if type(phiB) == np.ndarray:
            phiB[phiB < 0] += 360.
        dphi = phiA - phiB

        axes = self.alazar_axes(A.shape)

        ret = OrderedDict({
            "chanA_I" : {"unit" : "V", "value" : A.real},
            "chanA_Q" : {"unit" : "V", "value" : A.imag},
            "chanB_I" : {"unit" : "V", "value" : B.real},
            "chanB_Q" : {"unit" : "V", "value" : B.imag},
            "chanA_abs" : {"unit" : "V", "value" : abs(A), },
            "chanB_abs" : {"unit" : "V", "value" : abs(B), },
            "delta_abs" : {"unit" : "V", "value" : abs(A) - abs(B), },
            "chanA_phase" : {"unit" : "deg", "value" : phiA},
            "chanB_phase" : {"unit" : "deg", "value" : phiB },
            "delta_phase" : {"unit" : "deg", "value" : dphi },
            "abs" : {"unit" : "V", "value" : (abs(A)**2 + abs(B)**2)**.5, },
        })

        for k, v in axes.items():
            ret[k] = v

        return ret


class AWGGateSweep(Reflectometry, PysweepGrid):

    controller_cls = TrigController

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        self.add_parameter('gate_pts', Parameter, initial_value=200)
        self.ats_average_records(False)


    def setup(self):
        self.controller_cls.fg = self.station.fg
        self.station.fg.ch1_output_enabled(False)
        self.ats_records_per_buffer(self.gate_pts())
        super().setup()


    def cleanup(self):
        self.station.fg.ch1_output_enabled(False)