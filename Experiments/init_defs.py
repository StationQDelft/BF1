import time
from collections import OrderedDict
import numpy as np

from qcodes.instrument_drivers.AlazarTech.acq_controllers import ATS9360Controller

from pulsar.awg import awg5014

from stationq.qctools import instruments as instools
from stationq.data.data_storage import Data, GridData
from stationq.experiment.measurement import Parameter, BaseMeasurement, PysweepGrid
from stationq.experiment.ATS import AlazarMeasurement


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


class AWGMeasurement(BaseMeasurement):

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        self.awghandler = awg5014.AWG5014Handler(self.station.awg)

    def awg_sequence(self):
        raise NotImplementedError

    def setup_awg(self):
        self.awghandler.awg_settings.update(self.namespace.awg_settings)
        self.awghandler.program_awg(self.awg_sequence())

        for i in range(1,5):
            self.station.awg.set(f"ch{i}_state", 1)

        self.station.awg.start()
        time.sleep(0.1)

        nretry = 0
        while self.station.awg.state() != 'Waiting for trigger':
            logger.info('Waiting for AWG to get ready...')
            if nretry > 3:
                raise RuntimeError(f'AWG not started after {nretry} seconds.')
            time.sleep(1)

    def setup(self):
        super().setup()
        self.setup_awg()


class SimpleAWGRamp(AWGMeasurement):

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        self.add_parameter('ramp_pts', Parameter, initial_value=11)
        self.add_parameter('max_val', Parameter, initial_value=0.1)
        self.add_parameter('val_len', Parameter, initial_value=1e-7)
        self.add_parameter('ramp_down_len', Parameter, initial_value=1e-6)
        self.add_parameter('awg_chan', Parameter, initial_value=2)

    def awg_sequence(self):
        h = self.awghandler
        chan = self.awg_chan()

        samples_per_val = h.time_to_samples(self.val_len())
        samples_ramp_down = h.time_to_samples(self.ramp_down_len())
        vals = np.linspace(0, h.voltage_to_wfscale()[self.awg_chan()-1] * self.max_val(), self.ramp_pts())

        wf = np.zeros((self.ramp_pts()*samples_per_val+samples_ramp_down,),
                      dtype=h.get_awg_wf_dtype(chans=[chan]))

        for i, v in enumerate(vals):
            idx0, idx1 = i*samples_per_val, (i+1)*samples_per_val
            wf[f'ch{chan}_wf'][idx0:idx1] = v
            wf[f'ch{chan}_m1'][idx0:idx0+1] = 1
        wf[f'ch{chan}_wf'][idx1:] = np.linspace(v, 0, samples_ramp_down)

        return [dict(wf=wf)]

class TrigController(ATS9360Controller):
    fg = None

    def pre_acquire(self):
        time.sleep(1e-3)
        self.fg.ch1_output_enabled(True)

    def post_acquire(self):
        self.fg.ch1_output_enabled(False)
        time.sleep(5e-3)
        return super().post_acquire()


class AWGGateSweep(SimpleAWGRamp, Reflectometry, PysweepGrid):

    controller_cls = TrigController

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        self.ats_average_records(False)


    def setup(self):
        # setting up basic triggering
        self.controller_cls.fg = self.station.fg
        self.station.fg.ch1_output_enabled(False)

        # setting up alazar
        # first determine how long we integrate, and if we can fit more integration time into
        # the time of a record
        self.ats_records_per_buffer(self.ramp_pts())
        self.setup_alazar()

        # TODO: can this go into the alazar class?
        # idea: we interpret integration time as the minimal one, and then see
        # how much time a record will actually take. then adjust.
        logger.info(f'Samples per record: {self.samples_per_record}')
        rectime = self.samples_per_record / float(self.namespace.ats_settings['sample_rate'])
        if rectime - self.ats_int_time() > 1e-6:
            old_int_time = self.ats_int_time()
            self.ats_int_time((rectime - 1e-6)//(1./self.IF()) * 1./self.IF())
            self.setup_alazar()
        logger.info(f'Updated integration time: {self.ats_int_time()}')
        logger.info(f'Updated samples per record: {self.samples_per_record}')

        # time per gate voltage setting is a little longer than the record time
        vlen = (self.ats_int_time()//10e-6 + 1) * 10e-6
        self.val_len(vlen)
        logger.info(f'Time per gate voltage: {vlen} s')

        linetime = vlen * self.ramp_pts() + self.ramp_down_len()
        logger.info(f'Time per AWG sweep: {linetime} s')

        super().setup()

    def cleanup(self):
        self.station.fg.ch1_output_enabled(False)